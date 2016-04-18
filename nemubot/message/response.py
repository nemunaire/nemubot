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

from nemubot.message.abstract import Abstract


class Response(Abstract):

    def __init__(self, cmd, args=None, *nargs, **kargs):
        super().__init__(*nargs, **kargs)

        self.cmd = cmd
        self.args = args if args is not None else list()

    def __str__(self):
        return self.cmd + " @" + ",@".join(self.args)

    @property
    def cmds(self):
        # TODO: this is for legacy modules
        return [self.cmd] + self.args
