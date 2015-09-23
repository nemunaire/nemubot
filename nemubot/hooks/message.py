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

import re

from nemubot.hooks.abstract import Abstract
import nemubot.message


class Message(Abstract):

    """Class storing hook information, specialized for a generic Message"""

    def __init__(self, call, name=None, regexp=None, channels=list(),
                 server=None, help=None, help_usage=dict(), **kargs):

        Abstract.__init__(self, call=call, **kargs)

        assert regexp is None or type(regexp) is str, regexp
        assert channels is None or type(channels) is list, channels
        assert server is None or type(server) is str, server
        assert type(help_usage) is dict, help_usage

        self.name = str(name) if name is not None else None
        self.regexp = regexp
        self.server = server
        self.channels = channels
        self.help = help
        self.help_usage = help_usage


    def __str__(self):
        return "\x03\x02%s\x03\x02%s%s" % (
            self.name if self.name is not None else "\x03\x1f" + self.regexp + "\x03\x1f" if self.regexp is not None else "",
            " (restricted to %s)" % (self.server + ":" if self.server is not None else "") + (self.channels if self.channels else "*") if len(self.channels) or self.server else "",
            ": %s" % self.help if self.help is not None else ""
        )


    def match(self, msg, server=None):
        if not isinstance(msg, nemubot.message.abstract.Abstract):
            return True

        elif isinstance(msg, nemubot.message.Command):
            return self.is_matching(msg.cmd, msg.to, server)
        elif isinstance(msg, nemubot.message.Text):
            return self.is_matching(msg.message, msg.to, server)
        else:
            return False


    def is_matching(self, strcmp, receivers=list(), server=None):
        """Test if the current hook correspond to the message"""
        if ((server is None or self.server is None or self.server == server)
            and ((self.name is None or strcmp == self.name) and (
                self.regexp is None or re.match(self.regexp, strcmp)))):

            if receivers and self.channels:
                for receiver in receivers:
                    if receiver in self.channels:
                        return True
            else:
                return True
        return False
