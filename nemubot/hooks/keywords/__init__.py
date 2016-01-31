# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2016  Mercier Pierre-Olivier
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

from nemubot.exception.keyword import KeywordException
from nemubot.hooks.keywords.abstract import Abstract


class NoKeyword(Abstract):

    def check(self, mkw):
        if len(mkw):
            raise KeywordException("This command doesn't take any keyword arguments.")
        return super().check(mkw)


def reload():
    import imp

    import nemubot.hooks.keywords.abstract
    imp.reload(nemubot.hooks.keywords.abstract)

    import nemubot.hooks.keywords.dict
    imp.reload(nemubot.hooks.keywords.dict)
