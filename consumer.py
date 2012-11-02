# -*- coding: utf-8 -*-

# Nemubot is a modulable IRC bot, built around XML configuration files.
# Copyright (C) 2012  Mercier Pierre-Olivier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import queue
import re
import threading
import traceback
import sys

import bot
from message import Message
from response import Response
import server

class MessageConsumer:
    """Store a message before treating"""
    def __init__(self, srv, raw, time, prvt, data):
        self.srv = srv
        self.raw = raw
        self.time = time
        self.prvt = prvt
        self.data = data

    def treat_in(self, context, msg):
        """Treat the input message"""
        if msg.cmd == "PING":
            self.srv.send_pong(msg.content)
        else:
            # TODO: Manage credits here
            context.treat_pre(msg)

            if msg.cmd == "PRIVMSG" and msg.ctcp:
                if msg.cmds[0] in context.ctcp_capabilities:
                    return context.ctcp_capabilities[msg.cmds[0]](self.srv, msg)
                else:
                    return bot._ctcp_response(msg.sender, "ERRMSG Unknown or unimplemented CTCP request")
            elif msg.cmd == "PRIVMSG" and self.srv.accepted_channel(msg.channel):
                return self.treat_prvmsg(context, msg)
            # TODO: continue here
                pass

    def treat_prvmsg(self, context, msg):
        # Treat all messages starting with 'nemubot:' as distinct commands
        if msg.content.find("%s:"%self.srv.nick) == 0:
            # Remove the bot name
            msg.content = msg.content[len(self.srv.nick)+1:].strip()

            # Treat ping
            if re.match(".*(m[' ]?entends?[ -]+tu|h?ear me|do you copy|ping)",
                        msg.content, re.I) is not None:
                return Response(msg.sender, message="pong",
                                channel=msg.channel, nick=msg.nick)

            # Ask hooks
            else:
                return context.treat_ask(self)


    def treat_out(self, context, res):
        """Treat the output message"""
        # Define the destination server
        if (res.server is not None and
            res.server.instanceof(string) and res.server in context.servers):
            res.server = context.servers[res.server]
        if (res.server is not None and
            not res.server.instanceof(server.Server)):
            print ("\033[1;35mWarning:\033[0m the server defined in this "
                   "response doesn't exist: %s" % (res.server))
            res.server = None
        if res.server is None:
            res.server = self.srv

        # Sent the message only if treat_post authorize it
        if context.treat_post(res):
            res.server.send_response(res, self.data)

    def run(self, context):
        """Create, parse and treat the message"""
        try:
            msg = Message(self.srv, self.raw, self.time, self.prvt)
            res = self.treat_in(context, msg)
        except:
            print ("\033[1;31mERROR:\033[0m occurred during the "
                   "processing of the message: %s" % self.raw)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value,
                                      exc_traceback)
            return

        # Send message
        if res is not None:
            if isinstance(res, list):
                for r in res:
                    if isinstance(r, Response):
                        self.treat_out(context, r)
                    elif isinstance(r, list):
                        for s in r:
                            if isinstance(s, Response):
                                self.treat_out(context, s)
            elif isinstance(res, Response):
                self.treat_out(context, res)

        # Inform that the message has been treated
        self.srv.msg_treated(self.data)


class EventConsumer:
    """Store a event before treating"""
    def __init__(self, evt, timeout=20):
        self.evt = evt
        self.timeout = timeout

    def run(self, context):
        try:
            self.evt.launch_check()
        except:
            print ("\033[1;31mError:\033[0m during event end")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value,
                                      exc_traceback)
        if self.evt.next is not None:
            context.add_event(self.evt, self.evt.id)



class Consumer(threading.Thread):
    """Dequeue and exec requested action"""
    def __init__(self, context):
        self.context = context
        self.stop = False
        threading.Thread.__init__(self)

    def run(self):
        try:
            while not self.stop:
                stm = self.context.cnsr_queue.get(True, 20)
                stm.run(self.context)

        except queue.Empty:
            pass
        finally:
            self.context.cnsr_thrd_size -= 2
