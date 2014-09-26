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

from hooks import hook

nemubotversion = 3.4

logger = logging.getLogger("nemubot.response")

class Response:
    def __init__(self, message=None, channel=None, nick=None, server=None,
                 nomore="No more message", title=None, more="(suite) ",
                 count=None, ctcp=False, shown_first_count=-1,
                 line_treat=None):
        self.nomore = nomore
        self.more = more
        self.line_treat = line_treat
        self.rawtitle = title
        self.server = server
        self.messages = list()
        self.alone = True
        self.is_ctcp = ctcp
        if message is not None:
            self.append_message(message, shown_first_count=shown_first_count)
        self.elt = 0 # Next element to display

        self.sender = None
        self.channel = channel
        self.nick = nick
        self.count = count

    @property
    def receivers(self):
        if self.channel is None:
            if self.nick is not None:
                return [ self.nick ]
            return [ self.sender.split("!")[0] ]
        elif isinstance(self.channel, list):
            return self.channel
        else:
            return [ self.channel ]

    def set_sender(self, sender):
        if sender is None or sender.find("!") < 0:
            if sender is not None:
                logger.warn("Bad sender provided in Response, it will be ignored.", stack_info=True)
            self.sender = None
        else:
            self.sender = sender

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

    def treat_ctcp(self, content):
        if self.is_ctcp:
            return "\x01" + content + "\x01"
        else:
            return content

    def get_message(self):
        if self.alone and len(self.messages) > 1:
            self.alone = False

        if self.empty:
            return self.treat_ctcp(self.nomore)

        if self.line_treat is not None and self.elt == 0:
            self.messages[0] = self.line_treat(self.messages[0]).replace("\n", " ").strip()

        msg = ""
        if self.channel is not None and self.nick is not None:
            msg += self.nick + ": "

        if self.title is not None:
            if self.elt > 0:
                msg += self.title + " " + self.more + ": "
            else:
                msg += self.title + ": "

        if self.elt > 0:
            msg += "[…] "

        elts = self.messages[0][self.elt:]
        if isinstance(elts, list):
            for e in elts:
                if len(msg) + len(e) > 430:
                    msg += "[…]"
                    self.alone = False
                    return self.treat_ctcp(msg)
                else:
                    msg += e + ", "
                    self.elt += 1
            self.pop()
            return self.treat_ctcp(msg[:len(msg)-2])

        else:
            if len(elts.encode()) <= 432:
                self.pop()
                if self.count is not None:
                    return self.treat_ctcp(msg + elts + (self.count % len(self.messages)))
                else:
                    return self.treat_ctcp(msg + elts)

            else:
                words = elts.split(' ')

                if len(words[0].encode()) > 432 - len(msg.encode()):
                    self.elt += 432 - len(msg.encode())
                    return self.treat_ctcp(msg + elts[:self.elt] + "[…]")

                for w in words:
                    if len(msg.encode()) + len(w.encode()) > 431:
                        msg += "[…]"
                        self.alone = False
                        return self.treat_ctcp(msg)
                    else:
                        msg += w + " "
                        self.elt += len(w) + 1
                self.pop()
                return self.treat_ctcp(msg)


SERVERS = dict()

@hook("all_post")
def parseresponse(res):
    # TODO: handle inter-bot communication NOMORE
    # TODO: check that the response is not the one already saved
    rstr = res.get_message()

    if not res.alone:
        if res.server not in SERVERS:
            SERVERS[res.server] = dict()
        for receiver in res.receivers:
            SERVERS[res.server][receiver] = res

    ret = list()
    for channel in res.receivers:
        ret.append("%s %s :%s" % ("NOTICE" if res.is_ctcp else "PRIVMSG", channel, rstr))
    return ret


@hook("cmd_hook", "more")
def cmd_more(msg):
    """Display next chunck of the message"""
    res = list()
    if msg.server in SERVERS:
        for receiver in msg.receivers:
            if receiver in SERVERS[msg.server]:
                res.append(SERVERS[msg.server][receiver])
    return res


@hook("cmd_hook", "next")
def cmd_next(msg):
    """Display the next information include in the message"""
    res = list()
    if msg.server in SERVERS:
        for receiver in msg.receivers:
            if receiver in SERVERS[msg.server]:
                SERVERS[msg.server][receiver].pop()
                res.append(SERVERS[msg.server][receiver])
    return res
