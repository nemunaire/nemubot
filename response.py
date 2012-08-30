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

class Response:
    def __init__(self, message=None, channel=None, nick=None, server=None,
                 nomore="No more message", title=None, more="(suite) "):
        self.nomore = nomore
        self.more = more
        self.title = title
        self.messages = list()
        if message is not None:
            self.messages.append(message)
        self.elt = 0 # Next element to display

        self.channel = channel
        self.nick = nick
        self.alone = True

    def append_message(self, message):
        self.alone = False
        self.messages.append(message)

    @property
    def empty(self):
        return len(self.messages) <= 0

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
            msg += "... "

        elts = self.messages[0][self.elt:]
        if isinstance(elts, list):
            for e in elts:
                if len(msg) + len(e) > 430:
                    msg += "..."
                    self.alone = False
                    return msg
                else:
                    msg += e + ", "
                    self.elt += 1
            self.messages.pop(0)
            self.elt = 0
            return msg[:len(msg)-2]

        else:
            if len(elts) <= 432:
                self.messages.pop(0)
                self.elt = 0
                return msg + elts

            else:
                words = elts.split(' ')

                if len(words[0]) > 432 - len(msg):
                    self.elt += 432 - len(msg)
                    return msg + elts[:self.elt] + "..."

                for w in words:
                    if len(msg) + len(w) > 431:
                        msg += "..."
                        self.alone = False
                        return msg
                    else:
                        msg += w + " "
                        self.elt += len(w) + 1
                self.messages.pop(0)
                self.elt = 0
                return msg
