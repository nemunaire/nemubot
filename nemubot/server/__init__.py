# -*- coding: utf-8 -*-

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


# Lists for select
_rlist = []
_wlist = []
_xlist = []


def reload():
    import imp

    import nemubot.server.abstract
    imp.reload(nemubot.server.abstract)

    import nemubot.server.socket
    imp.reload(nemubot.server.socket)

    import nemubot.server.IRC
    imp.reload(nemubot.server.IRC)
