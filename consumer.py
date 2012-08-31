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

class Consumer(threading.Thread):
    def __init__(self, context):
        self.context = context
        self.stop = False
        threading.Thread.__init__(self)

    def run(self):
        try:
            while not self.stop:
                (srv, raw, time, prvt, data) = self.context.msg_queue.get(True, 20)

                # Create, parse and treat the message
                try:
                    msg = Message(srv, raw, time, prvt)
                    res = msg.treat(self.context.hooks)
                except:
                    print ("\033[1;31mERROR:\033[0m occurred during the "
                           "processing of the message: %s" % raw)
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    traceback.print_exception(exc_type, exc_value,
                                              exc_traceback)
                    return

                # Send message
                if res is not None:
                    if isinstance(res, list):
                        for r in res:
                            if isinstance(r, Response):
                                srv.send_response(r, data)
                    elif isinstance(res, Response):
                        srv.send_response(res, data)

        except queue.Empty:
            pass
        finally:
            self.context.msg_thrd_size -= 2
