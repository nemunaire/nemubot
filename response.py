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

import traceback
import sys

class Response:
    def __init__(self, sender, message=None, channel=None, nick=None, server=None,
                 nomore="No more message", title=None, more="(suite) ", count=None,
                 ctcp=False, shown_first_count=-1):
        self.nomore = nomore
        self.more = more
        self.rawtitle = title
        self.server = server
        self.messages = list()
        self.alone = True
        self.ctcp = ctcp
        if message is not None:
            self.append_message(message, shown_first_count=shown_first_count)
        self.elt = 0 # Next element to display

        self.channel = channel
        self.nick = nick
        self.set_sender(sender)
        self.count = count

    @property
    def content(self):
        #FIXME: error when messages in self.messages are list!
        try:
            if self.title is not None:
                return self.title + ", ".join(self.messages)
            else:
                return ", ".join(self.messages)
        except:
            return ""

    def set_sender(self, sender):
        if sender is None or sender.find("!") < 0:
            if sender is not None:
                print("\033[1;35mWarning:\033[0m bad sender provided in Response, it will be ignored.")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback)
            self.sender = None
        else:
            self.sender = sender

    def append_message(self, message, title=None, shown_first_count=-1):
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
        if isinstance(self.rawtitle, list):
            self.rawtitle.pop(0)
            if len(self.rawtitle) <= 0:
                self.rawtitle = None

    def get_message(self):
        if self.alone and len(self.messages) > 1:
            self.alone = False

        if self.empty:
            return self.nomore

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
                    return msg
                else:
                    msg += e + ", "
                    self.elt += 1
            self.pop()
            self.elt = 0
            return msg[:len(msg)-2]

        else:
            if len(elts) <= 432:
                self.pop()
                self.elt = 0
                if self.count is not None:
                    return msg + elts + (self.count % len(self.messages))
                else:
                    return msg + elts

            else:
                words = elts.split(' ')

                if len(words[0]) > 432 - len(msg):
                    self.elt += 432 - len(msg)
                    return msg + elts[:self.elt] + "[…]"

                for w in words:
                    if len(msg) + len(w) > 431:
                        msg += "[…]"
                        self.alone = False
                        return msg
                    else:
                        msg += w + " "
                        self.elt += len(w) + 1
                self.pop()
                self.elt = 0
                return msg

import hooks
class Hook:
    def __init__(self, TYPE, call, name=None, data=None, regexp=None,
                 channels=list(), server=None, end=None, call_end=None,
                 SRC=None):
        self.hook = hooks.Hook(call, name, data, regexp, channels,
                               server, end, call_end)
        self.type = TYPE
        self.src = SRC
