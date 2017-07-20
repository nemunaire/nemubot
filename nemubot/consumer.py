# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2016  Mercier Pierre-Olivier
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
import threading

logger = logging.getLogger("nemubot.consumer")


class MessageConsumer:

    """Store a message before treating"""

    def __init__(self, srv, msg):
        self.srv = srv
        self.orig = msg


    def run(self, context):
        """Create, parse and treat the message"""

        from nemubot.bot import Bot
        assert isinstance(context, Bot)

        msgs = []

        # Parse message
        try:
            for msg in self.srv.parse(self.orig):
                msgs.append(msg)
        except:
            logger.exception("Error occurred during the processing of the %s: "
                             "%s", type(self.orig).__name__, self.orig)

        # Treat message
        for msg in msgs:
            for res in context.treater.treat_msg(msg):
                # Identify destination
                to_server = None
                if isinstance(res, str):
                    to_server = self.srv
                elif not hasattr(res, "server"):
                    logger.error("No server defined for response of type %s: %s", type(res).__name__, res)
                    continue
                elif res.server is None:
                    to_server = self.srv
                    res.server = self.srv.fileno()
                elif res.server in context.servers:
                    to_server = context.servers[res.server]
                else:
                    to_server = res.server

                if to_server is None or not hasattr(to_server, "send_response") or not callable(to_server.send_response):
                    logger.error("The server defined in this response doesn't exist: %s", res.server)
                    continue

                # Sent message
                to_server.send_response(res)


class EventConsumer:

    """Store a event before treating"""

    def __init__(self, evt, timeout=20):
        self.evt = evt
        self.timeout = timeout


    def run(self, context):
        try:
            self.evt.check()
        except:
            logger.exception("Error during event end")

        # Reappend the event in the queue if it has next iteration
        if self.evt.next():
            context.add_event(self.evt)



class Consumer(threading.Thread):

    """Dequeue and exec requested action"""

    def __init__(self, context):
        self.context = context
        self.stop = False
        super().__init__(name="Nemubot consumer")


    def run(self):
        try:
            while not self.stop:
                stm = self.context.cnsr_queue.get(True, 1)
                stm.run(self.context)
                self.context.cnsr_queue.task_done()

        except queue.Empty:
            pass
        finally:
            self.context.cnsr_thrd_size -= 2
            self.context.cnsr_thrd.remove(self)
