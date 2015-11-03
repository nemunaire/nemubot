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

def get_boolean(s):
    if isinstance(s, bool):
        return s
    else:
        return (s and s != "0" and s.lower() != "false" and s.lower() != "off")

from nemubot.config.include import Include
from nemubot.config.module import Module
from nemubot.config.nemubot import Nemubot
from nemubot.config.server import Server

def reload():
    global Include, Module, Nemubot, Server

    import imp

    import nemubot.config.include
    imp.reload(nemubot.config.include)
    Include = nemubot.config.include.Include

    import nemubot.config.module
    imp.reload(nemubot.config.module)
    Module = nemubot.config.module.Module

    import nemubot.config.nemubot
    imp.reload(nemubot.config.nemubot)
    Nemubot = nemubot.config.nemubot.Nemubot

    import nemubot.config.server
    imp.reload(nemubot.config.server)
    Server = nemubot.config.server.Server
