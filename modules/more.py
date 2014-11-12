# -*- coding: utf-8 -*-

# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2014  nemunaire
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

"""Progressive display of very long messages"""

import logging

from message import TextMessage, DirectAsk
from hooks import hook

nemubotversion = 3.4

logger = logging.getLogger("nemubot.response")

class Response:
    def __init__(self, message=None, channel=None, nick=None, server=None,
                 nomore="No more message", title=None, more="(suite) ",
                 count=None, shown_first_count=-1, line_treat=None):
        self.nomore = nomore
        self.more = more
        self.line_treat = line_treat
        self.rawtitle = title
        self.server = server
        self.messages = list()
        self.alone = True
        if message is not None:
            self.append_message(message, shown_first_count=shown_first_count)
        self.elt = 0 # Next element to display

        self.channel = channel
        self.nick = nick
        self.count = count

    @property
    def receivers(self):
        if self.channel is None:
            if self.nick is not None:
                return [ self.nick ]
            return list()
        elif isinstance(self.channel, list):
            return self.channel
        else:
            return [ self.channel ]

    def append_message(self, message, title=None, shown_first_count=-1):
        if type(message) is str:
            message = message.split('\n')
            if len(message) > 1:
                for m in message:
                    self.append_message(m)
                return
            else:
                message = message[0]
        if message is not None and len(message) > 0:
            if shown_first_count >= 0:
                self.messages.append(message[:shown_first_count])
                message = message[shown_first_count:]
            self.messages.append(message)
            self.alone = self.alone and len(self.messages) <= 1
            if isinstance(self.rawtitle, list):
                self.rawtitle.append(title)
            elif title is not None:
                rawtitle = self.rawtitle
                self.rawtitle = list()
                for osef in self.messages:
                    self.rawtitle.append(rawtitle)
                self.rawtitle.pop()
                self.rawtitle.append(title)

    def append_content(self, message):
        if message is not None and len(message) > 0:
            if self.messages is None or len(self.messages) == 0:
                self.messages = list(message)
                self.alone = True
            else:
                self.messages[len(self.messages)-1] += message
                self.alone = self.alone and len(self.messages) <= 1

    @property
    def empty(self):
        return len(self.messages) <= 0

    @property
    def title(self):
        if isinstance(self.rawtitle, list):
            return self.rawtitle[0]
        else:
            return self.rawtitle

    def pop(self):
        self.messages.pop(0)
        self.elt = 0
        if isinstance(self.rawtitle, list):
            self.rawtitle.pop(0)
            if len(self.rawtitle) <= 0:
                self.rawtitle = None


    def accept(self, visitor):
        visitor.visit(self.next_response())


    def next_response(self, maxlen=440):
        if self.nick:
            return DirectAsk(self.nick, self.get_message(maxlen - len(self.nick) - 2), server=None, to=self.receivers)
        else:
            return TextMessage(self.get_message(maxlen), server=None, to=self.receivers)


    def get_message(self, maxlen):
        if self.alone and len(self.messages) > 1:
            self.alone = False

        if self.empty:
            if hasattr(self.nomore, '__call__'):
                res = self.nomore(self)
                if res is None:
                    return "No more message"
                elif isinstance(res, Response):
                    self.__dict__ = res.__dict__
                elif isinstance(res, list):
                    self.messages = res
                elif isinstance(res, str):
                    self.messages.append(res)
                else:
                    raise Exception("Type returned by nomore (%s) is not handled here." % type(res))
                return self.get_message()
            else:
                return self.nomore

        if self.line_treat is not None and self.elt == 0:
            self.messages[0] = self.line_treat(self.messages[0]).replace("\n", " ").strip()

        msg = ""
        if self.title is not None:
            if self.elt > 0:
                msg += self.title + " " + self.more + ": "
            else:
                msg += self.title + ": "

        elif self.elt > 0:
            msg += "[…] "

        elts = self.messages[0][self.elt:]
        if isinstance(elts, list):
            for e in elts:
                if len(msg) + len(e) > maxlen - 3:
                    msg += "[…]"
                    self.alone = False
                    return msg
                else:
                    msg += e + ", "
                    self.elt += 1
            self.pop()
            return msg[:len(msg)-2]

        else:
            if len(elts.encode()) <= maxlen:
                self.pop()
                if self.count is not None:
                    return msg + elts + (self.count % len(self.messages))
                else:
                    return msg + elts

            else:
                words = elts.split(' ')

                if len(words[0].encode()) > maxlen - len(msg.encode()):
                    self.elt += maxlen - len(msg.encode())
                    return msg + elts[:self.elt] + "[…]"

                for w in words:
                    if len(msg.encode()) + len(w.encode()) >= maxlen:
                        msg += "[…]"
                        self.alone = False
                        return msg
                    else:
                        msg += w + " "
                        self.elt += len(w) + 1
                self.pop()
                return msg


SERVERS = dict()

@hook("all_post")
def parseresponse(res):
    # TODO: handle inter-bot communication NOMORE
    # TODO: check that the response is not the one already saved
    if isinstance(res, Response):
        if res.server not in SERVERS:
            SERVERS[res.server] = dict()
        for receiver in res.receivers:
            if receiver in SERVERS[res.server]:
                nw, bk = SERVERS[res.server][receiver]
            else:
                nw, bk = None, None
            if nw != res:
                SERVERS[res.server][receiver] = (res, bk)
    return res


@hook("cmd_hook", "more")
def cmd_more(msg):
    """Display next chunck of the message"""
    res = list()
    if msg.server in SERVERS:
        for receiver in msg.to_response:
            if receiver in SERVERS[msg.server]:
                nw, bk = SERVERS[msg.server][receiver]
                if nw is not None and not nw.alone:
                    bk = nw
                    SERVERS[msg.server][receiver] = None, bk
                if bk is not None:
                    res.append(bk)
    return res


@hook("cmd_hook", "next")
def cmd_next(msg):
    """Display the next information include in the message"""
    res = list()
    if msg.server in SERVERS:
        for receiver in msg.to_response:
            if receiver in SERVERS[msg.server]:
                nw, bk = SERVERS[msg.server][receiver]
                if nw is not None and not nw.alone:
                    bk = nw
                    SERVERS[msg.server][receiver] = None, bk
                bk.pop()
                if bk is not None:
                    res.append(bk)
    return res
