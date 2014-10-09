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

import imp

def intToIP(n):
    ip = ""
    for i in range(0,4):
        mod = n % 256
        ip = "%d.%s" % (mod, ip)
        n = (n - mod) / 256
    return ip[:len(ip) - 1]

def ipToInt(ip):
    sum = 0
    for b in ip.split("."):
        sum = 256 * sum + int(b)
    return sum


def reload():
    import tools.countdown
    imp.reload(tools.countdown)

    import tools.date
    imp.reload(tools.date)

    import tools.web
    imp.reload(tools.web)
