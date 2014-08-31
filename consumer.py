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

import logging
import queue
import re
import threading
import traceback
import sys

import bot
from server.DCC import DCC
from message import Message
import response
import server

logger = logging.getLogger("nemubot.consumer")

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
            self.srv.write("%s :%s" % ("PONG", msg.params[0]))
        elif hasattr(msg, "receivers"):
            if msg.receivers:
                # All messages
                context.treat_pre(msg, self.srv)

                return context.treat_irc(msg, self.srv)

    def treat_out(self, context, res):
        """Treat the output message"""
        if isinstance(res, list):
            for r in res:
                if r is not None: self.treat_out(context, r)

        elif isinstance(res, response.Response):
            # Define the destination server
            to_server = None
            if res.server is None:
                to_server = self.srv
                res.server = self.srv.id
            elif isinstance(res.server, str) and res.server in context.servers:
                to_server = context.servers[res.server]

            if to_server is None:
                logger.error("The server defined in this response doesn't "
                             "exist: %s", res.server)
                return False

            # Sent the message only if treat_post authorize it
            if context.treat_post(res):
                if type(res.channel) != list:
                    res.channel = [ res.channel ]
                for channel in res.channel:
                    if channel is not None and channel != to_server.nick:
                        to_server.write("%s %s :%s" % ("PRIVMSG", channel, res.get_message()))
                    else:
                        channel = res.sender.split("!")[0]
                        to_server.write("%s %s :%s" % ("NOTICE" if res.is_ctcp else "PRIVMSG", channel, res.get_message()))

        elif res is not None:
            logger.error("Unrecognized response type: %s", res)

    def run(self, context):
        """Create, parse and treat the message"""
        try:
            msg = Message(self.raw, self.time, self.prvt)
            msg.server = self.srv.id
            if msg.cmd == "PRIVMSG":
                msg.is_owner = (msg.nick == self.srv.owner)
                msg.private = msg.private or (len(msg.receivers) == 1 and msg.receivers[0] == self.srv.nick)
            res = self.treat_in(context, msg)
        except:
            logger.exception("Error occurred during the processing of the message: %s", self.raw)
            return

        # Send message
        self.treat_out(context, res)

        # Inform that the message has been treated
        #self.srv.msg_treated(self.data)



class EventConsumer:
    """Store a event before treating"""
    def __init__(self, evt, timeout=20):
        self.evt = evt
        self.timeout = timeout


    def run(self, context):
        try:
            self.evt.launch_check()
        except:
            logger.exception("Error during event end")
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
                self.context.cnsr_queue.task_done()

        except queue.Empty:
            pass
        finally:
            self.context.cnsr_thrd_size -= 2
            self.context.cnsr_thrd.remove(self)
