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

import re

from exception import IRCException
import hooks

from message import Message

class MessageHook(hooks.AbstractHook):

    """Class storing hook information, specialized for a generic Message"""

    def __init__(self, call, name=None, data=None, regexp=None,
                 channels=list(), server=None, mtimes=-1, end_call=None):

        hooks.AbstractHook.__init__(self, call=call, data=data,
                                    end_call=end_call, mtimes=mtimes)

        self.name = name
        self.regexp = regexp
        self.server = server
        self.channels = channels


    def match(self, message, server=None):
        if not isinstance(message, Message):
            return True

        elif message.qual == "cmd":
            return self.is_matching(message.cmds[0], message.channel, server)
        elif hasattr(message, "text"):
            return self.is_matching(message.text, message.channel, server)
        elif len(message.params) > 0:
            return self.is_matching(message.params[0], message.channel, server)
        else:
            return self.is_matching(message.cmd, message.channel, server)


    def is_matching(self, strcmp, channel=None, server=None):
        """Test if the current hook correspond to the message"""
        return (channel is None or len(self.channels) <= 0 or
                channel in self.channels) and (server is None or
             self.server is None or self.server == server) and (
            (self.name is None or strcmp == self.name) and (
            self.regexp is None or re.match(self.regexp, strcmp)))
