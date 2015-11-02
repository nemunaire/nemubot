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

from nemubot.hooks.message import Message
from nemubot.hooks.keywords import NoKeyword
from nemubot.hooks.keywords.abstract import Abstract as AbstractKeywords
from nemubot.hooks.keywords.dict import Dict as DictKeywords
import nemubot.message


class Command(Message):

    """Class storing hook information, specialized for Command messages"""

    def __init__(self, call, name=None, help_usage=dict(), keywords=NoKeyword(),
                 **kargs):

        super().__init__(call=call, **kargs)

        if isinstance(keywords, dict):
            keywords = DictKeywords(keywords)

        assert type(help_usage) is dict, help_usage
        assert isinstance(keywords, AbstractKeywords), keywords

        self.name = str(name) if name is not None else None
        self.help_usage = help_usage
        self.keywords = keywords


    def __str__(self):
        return "\x03\x02%s\x03\x02%s%s" % (
            self.name if self.name is not None else "\x03\x1f" + self.regexp + "\x03\x1f" if self.regexp is not None else "",
            " (restricted to %:%s)" % ((",".join(self.servers) if self.server else "*") + (",".join(self.channels) if self.channels else "*")) if len(self.channels) or len(self.servers) else "",
            ": %s" % self.help if self.help is not None else ""
        )


    def check(self, msg):
        return self.keywords.check(msg.kwargs) and super().check(msg)


    def match(self, msg):
        if not isinstance(msg, nemubot.message.command.Command):
            return False
        else:
            return (
                (self.name is None or msg.cmd == self.name) and
                (self.regexp is None or re.match(self.regexp, msg.cmd))
            )
