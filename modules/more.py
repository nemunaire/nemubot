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

"""Progressive display of very long messages"""

from hooks import hook

nemubotversion = 3.4

SERVERS = dict()

@hook("all_post")
def parseresponse(res):
    # TODO: handle inter-bot communication NOMORE
    # TODO: check that the response is not the one already saved
    if not res.alone:
        if res.server not in SERVERS:
            SERVERS[res.server] = dict()
        for receiver in res.receivers:
            SERVERS[res.server][receiver] = res
    return res


@hook("cmd_hook", "more")
def cmd_more(msg):
    """Display next chunck of the message"""
    res = list()
    if msg.server in SERVERS:
        for receiver in msg.receivers:
            if receiver in SERVERS[msg.server]:
                res.append(SERVERS[msg.server][receiver])
    return res


@hook("cmd_hook", "next")
def cmd_next(msg):
    """Display the next information include in the message"""
    res = list()
    if msg.server in SERVERS:
        for receiver in msg.receivers:
            if receiver in SERVERS[msg.server]:
                SERVERS[msg.server][receiver].pop()
                res.append(SERVERS[msg.server][receiver])
    return res
