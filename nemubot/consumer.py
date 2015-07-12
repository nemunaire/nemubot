# -*- coding: utf-8 -*-

# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2015  Mercier Pierre-Olivier
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
        self.msgs = [ ]
        self.responses = None


    def first_treat(self, msg):
        """Qualify a new message/response

        Argument:
        msg -- The Message or Response to qualify
        """

        # Define the source server if not already done
        if not hasattr(msg, "server") or msg.server is None:
            msg.server = self.srv.id

        if hasattr(msg, "frm_owner"):
            msg.frm_owner = (not hasattr(self.srv, "owner") or self.srv.owner == msg.frm)

        return msg


    def pre_treat(self, hm):
        """Modify input Messages

        Arguments:
        hm -- Hooks manager
        """

        new_msg = list()
        new_msg += self.msgs
        self.msgs = list()

        while len(new_msg) > 0:
            msg = new_msg.pop(0)
            for h in hm.get_hooks("pre", type(msg).__name__):
                if h.match(msg, server=self.srv):
                    res = h.run(msg)
                    if isinstance(res, list):
                        for i in range(len(res)):
                            if res[i] == msg:
                                res.pop(i)
                                break
                        new_msg += res
                    elif res is not None and res != msg:
                        new_msg.append(res)
                        msg = None
                        break
                    elif res is None or res is False:
                        msg = None
                        break
            if msg is not None:
                self.msgs.append(msg)


    def in_treat(self, hm):
        """Treat Messages and store responses

        Arguments:
        hm -- Hooks manager
        """

        self.responses = list()
        for msg in self.msgs:
            for h in hm.get_hooks("in", type(msg).__name__):
                if h.match(msg, server=self.srv):
                    res = h.run(msg)
                    if isinstance(res, list):
                        self.responses += res
                    elif res is not None:
                        self.responses.append(res)


    def post_treat(self, hm):
        """Modify output Messages

        Arguments:
        hm -- Hooks manager
        """

        new_msg = list()
        new_msg += self.responses
        self.responses = list()

        while len(new_msg) > 0:
            ff = new_msg.pop(0)
            if isinstance(ff, str):
                self.responses.append(ff)
                continue
            msg = self.first_treat(ff)
            for h in hm.get_hooks("post"):
                if h.match(msg, server=self.srv):
                    res = h.run(msg)
                    if isinstance(res, list):
                        for i in range(len(res)):
                            if isinstance(res[i], str):
                                self.responses.append(res.pop(i))
                                break
                        msg = None
                        new_msg += res
                        break
                    elif res is not None and res != msg:
                        new_msg.append(res)
                        msg = None
                        break
                    elif res is None or res is False:
                        msg = None
                        break
                    else:
                        msg = res
            if msg is not None:
                self.responses.append(msg)


    def run(self, context):
        """Create, parse and treat the message"""
        try:
            for msg in self.srv.parse(self.orig):
                self.msgs.append(msg)
        except:
            logger.exception("Error occurred during the processing of the %s: "
                             "%s", type(self.msgs[0]).__name__, self.msgs[0])

        if len(self.msgs) <= 0:
            return

        try:
            for msg in self.msgs:
                self.first_treat(msg)

            # Run pre-treatment: from Message to [ Message ]
            self.pre_treat(context.hooks)

            # Run in-treatment: from Message to [ Response ]
            if len(self.msgs) > 0:
                self.in_treat(context.hooks)

            # Run post-treatment: from Response to [ Response ]
            if self.responses is not None and len(self.responses) > 0:
                self.post_treat(context.hooks)
        except BaseException as e:
            logger.exception("Error occurred during the processing of the %s: "
                             "%s", type(self.msgs[0]).__name__, self.msgs[0])

            from nemubot.message import Text
            self.responses.append(Text("Sorry, an error occured (%s). Feel free to open a new issue at https://github.com/nemunaire/nemubot/issues/new" % type(e).__name__,
                                       server=self.srv.id, to=self.msgs[0].to_response))

        for res in self.responses:
            to_server = None
            if isinstance(res, str):
                to_server = self.srv
            elif res.server is None:
                to_server = self.srv
                res.server = self.srv.id
            elif isinstance(res.server, str) and res.server in context.servers:
                to_server = context.servers[res.server]

            if to_server is None:
                logger.error("The server defined in this response doesn't "
                             "exist: %s", res.server)
                continue

            # Sent the message only if treat_post authorize it
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
        if self.evt.next is not None:
            context.add_event(self.evt, eid=self.evt.id)

        # Or remove reference of this event
        elif (hasattr(self.evt, "module_src") and
              self.evt.module_src is not None):
            self.evt.module_src.__nemubot_context__.events.remove(self.evt.id)



class Consumer(threading.Thread):
    """Dequeue and exec requested action"""
    def __init__(self, context):
        self.context = context
        self.stop = False
        threading.Thread.__init__(self)

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
