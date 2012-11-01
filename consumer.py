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
import threading
import traceback
import sys

from message import Message
from response import Response

class MessageConsumer:
    """Store a message before treating"""
    def __init__(self, srv, raw, time, prvt, data):
        self.srv = srv
        self.raw = raw
        self.time = time
        self.prvt = prvt
        self.data = data

    def run(self):
        # Create, parse and treat the message
        try:
            msg = Message(self.srv, self.raw, self.time, self.prvt)
            res = msg.treat()
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
                        self.srv.send_response(r, self.data)
                    elif isinstance(r, list):
                        for s in r:
                            if isinstance(s, Response):
                                self.srv.send_response(s, self.data)
            elif isinstance(res, Response):
                self.srv.send_response(res, self.data)
                
        # Inform that the message has been treated
        self.srv.msg_treated(self.data)
        

class EventConsumer:
    """Store a event before treating"""
    def __init__(self, context, evt, timeout=20):
        self.context = context
        self.evt = evt
        self.timeout = timeout

    def run(self):
        try:
            self.evt.launch_check()
        except:
            print ("\033[1;31mError:\033[0m during event end")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value,
                                      exc_traceback)
        if self.evt.next is not None:
            self.context.add_event(self.evt, self.evt.id)
        
        

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
                stm.run()

        except queue.Empty:
            pass
        finally:
            self.context.cnsr_thrd_size -= 2
