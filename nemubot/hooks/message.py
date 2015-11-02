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

    def __init__(self, call, regexp=None, help=None, **kwargs):
        super().__init__(call=call, **kwargs)

        assert regexp is None or type(regexp) is str, regexp

        self.regexp = regexp
        self.help = help


    def __str__(self):
        # TODO: find a way to name the feature (like command: help)
        return self.help if self.help is not None else super().__str__()


    def check(self, msg):
        return super().check(msg)


    def match(self, msg):
        if not isinstance(msg, nemubot.message.text.Text):
            return False
        else:
            return self.regexp is None or re.match(self.regexp, msg.message)
