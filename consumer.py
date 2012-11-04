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
from DCC import DCC
from message import Message
import response
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
            # All messages
            context.treat_pre(msg, self.srv)

            # TODO: Manage credits
            return context.treat_irc(msg, self.srv)

    def treat_out(self, context, res):
        """Treat the output message"""
        if isinstance(res, list):
            for r in res:
                if r is not None: self.treat_out(context, r)

        elif isinstance(res, response.Response):
        # Define the destination server
            if (res.server is not None and
                isinstance(res.server, str) and res.server in context.servers):
                res.server = context.servers[res.server]
            if (res.server is not None and
                not isinstance(res.server, server.Server)):
                print ("\033[1;35mWarning:\033[0m the server defined in this "
                       "response doesn't exist: %s" % (res.server))
                res.server = None
            if res.server is None:
                res.server = self.srv

            # Sent the message only if treat_post authorize it
            if context.treat_post(res):
                res.server.send_response(res, self.data)

        elif isinstance(res, response.Hook):
            context.hooks.add_hook(res.type, res.hook, res.src)

        elif res is not None:
            print ("\033[1;35mWarning:\033[0m unrecognized response type "
                   ": %s" % res)

    def run(self, context):
        """Create, parse and treat the message"""
        try:
            msg = Message(self.raw, self.time, self.prvt)
            if msg.cmd == "PRIVMSG":
                msg.is_owner = (msg.nick == self.srv.owner)
            res = self.treat_in(context, msg)
        except:
            print ("\033[1;31mERROR:\033[0m occurred during the "
                   "processing of the message: %s" % self.raw)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value,
                                      exc_traceback)
            return

        # Send message
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



def _help_msg(modules, sndr, cmd):
    """Parse and response to help messages"""
    res = response.Response(sndr)
    if len(cmd) > 1:
        if cmd[1] in modules:
            if len(cmd) > 2:
                if hasattr(modules[cmd[1]], "HELP_cmd"):
                    res.append_message(modules[cmd[1]].HELP_cmd(cmd[2]))
                else:
                    res.append_message("No help for command %s in module %s" % (cmd[2], cmd[1]))
            elif hasattr(modules[cmd[1]], "help_full"):
                res.append_message(modules[cmd[1]].help_full())
            else:
                res.append_message("No help for module %s" % cmd[1])
        else:
            res.append_message("No module named %s" % cmd[1])
    else:
        res.append_message("Pour me demander quelque chose, commencez "
                           "votre message par mon nom ; je réagis "
                           "également à certaine commandes commençant par"
                           " !.  Pour plus d'informations, envoyez le "
                           "message \"!more\".")
        res.append_message("Mon code source est libre, publié sous "
                           "licence AGPL (http://www.gnu.org/licenses/). "
                           "Vous pouvez le consulter, le dupliquer, "
                           "envoyer des rapports de bogues ou bien "
                           "contribuer au projet sur GitHub : "
                           "http://github.com/nemunaire/nemubot/")
        res.append_message(title="Pour plus de détails sur un module, "
                           "envoyez \"!help nomdumodule\". Voici la liste"
                           " de tous les modules disponibles localement",
                           message=["\x03\x02%s\x03\x02 (%s)" % (im, modules[im].help_tiny ()) for im in modules if hasattr(modules[im], "help_tiny")])
    return res
