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
import re

from response import Response
from exception import IRCException

logger = logging.getLogger("nemubot.hooks")

class Hook:
    """Class storing hook informations"""
    def __init__(self, call, name=None, data=None, regexp=None, channels=list(), server=None, end=None, call_end=None, help=None):
        self.name = name
        self.end = end
        self.call = call
        if call_end is None:
            self.call_end = self.call
        else:
            self.call_end = call_end
        self.regexp = regexp
        self.data = data
        self.times = -1
        self.server = server
        self.channels = channels
        self.help = help

    def match(self, message, channel=None, server=None):
        if isinstance(message, Response):
            return self.is_matching(None, channel, server)
        elif message.qual == "cmd":
            return self.is_matching(message.cmds[0], channel, server)
        elif hasattr(message, "text"):
            return self.is_matching(message.text, channel, server)
        elif len(message.params) > 0:
            return self.is_matching(message.params[0], channel, server)
        else:
            return self.is_matching(message.cmd, channel, server)

    def is_matching(self, strcmp, channel=None, server=None):
        """Test if the current hook correspond to the message"""
        return (channel is None or len(self.channels) <= 0 or
                channel in self.channels) and (server is None or
             self.server is None or self.server == server) and (
            (self.name is None or strcmp == self.name) and (
            self.end is None or strcmp == self.end) and (
            self.regexp is None or re.match(self.regexp, strcmp)))

    def run(self, msg, data2=None, strcmp=None):
        """Run the hook"""
        if self.times != 0:
            self.times -= 1

        if (self.end is not None and strcmp is not None and
            self.call_end is not None and strcmp == self.end):
            call = self.call_end
            self.times = 0
        else:
            call = self.call

        try:
            if self.data is None:
                if data2 is None:
                    return call(msg)
                elif isinstance(data2, dict):
                    return call(msg, **data2)
                else:
                    return call(msg, data2)
            elif isinstance(self.data, dict):
                if data2 is None:
                    return call(msg, **self.data)
                else:
                    return call(msg, data2, **self.data)
            else:
                if data2 is None:
                    return call(msg, self.data)
                elif isinstance(data2, dict):
                    return call(msg, self.data, **data2)
                else:
                    return call(msg, self.data, data2)
        except IRCException as e:
            return e.fill_response(msg)

last_registered = []

def hook(store, *args, **kargs):
    def sec(call):
        last_registered.append((store, Hook(call, *args, **kargs)))
        return call
    return sec
