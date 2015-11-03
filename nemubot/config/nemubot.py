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

from nemubot.config.include import Include
from nemubot.config.module import Module
from nemubot.config.server import Server


class Nemubot:

    def __init__(self, nick="nemubot", realname="nemubot", owner=None,
                 ip=None, ssl=False, caps=None, encoding="utf-8"):
        self.nick = nick
        self.realname = realname
        self.owner = owner
        self.ip = ip
        self.caps = caps.split(" ") if caps is not None else []
        self.encoding = encoding
        self.servers = []
        self.modules = []
        self.includes = []


    def addChild(self, name, child):
        if name == "module" and isinstance(child, Module):
            self.modules.append(child)
            return True
        elif name == "server" and isinstance(child, Server):
            self.servers.append(child)
            return True
        elif name == "include" and isinstance(child, Include):
            self.includes.append(child)
            return True
