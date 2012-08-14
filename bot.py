# -*- coding: utf-8 -*-

# Nemubot is a modulable IRC bot, built around XML configuration files.
# Copyright (C) 2012  Mercier Pierre-Olivier
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

import event
import hooks
from server import Server

class Bot:
    def __init__(self, servers=dict(), modules=dict(), mp=list()):
        self.version = 3.2
        self.version_txt = "3.2"

        self.servers = servers
        self.modules = modules

        self.modules_path = mp
        self.datas_path = './datas/'

        self.hooks = hooks.MessagesHook()
        self.events = list()


    def addServer(self, node, nick, owner, realname):
        """Add a new server to the context"""
        srv = Server(node, nick, owner, realname)
        if srv.id not in self.servers:
            self.servers[srv.id] = srv
            if srv.autoconnect:
                srv.launch(self)
            return True
        else:
            return False


    def add_module(self, module):
        """Add a module to the context, if already exists, unload the
        old one before"""
        # Check if the module already exists
        for mod in self.modules.keys():
            if self.modules[mod].name == module.name:
                self.unload_module(self.modules[mod].name)
                break

        self.modules[module.name] = module
        return True


    def add_modules_path(self, path):
        """Add a path to the modules_path array, used by module loader"""
        # The path must end by / char
        if path[len(path)-1] != "/":
            path = path + "/"

        if path not in self.modules_path:
            self.modules_path.append(path)
            return True

        return False


    def unload_module(self, name, verb=False):
        """Unload a module"""
        if name in self.modules:
            self.modules[name].save()
            if hasattr(self.modules[name], "unload"):
                self.modules[name].unload()
            # Remove from the dict
            del self.modules[name]
            return True
        return False


    def quit(self, verb=False):
        """Save and unload modules and disconnect servers"""
        if verb: print ("Save and unload all modules...")
        k = list(self.modules.keys())
        for mod in k:
            self.unload_module(mod, verb)

        if verb: print ("Close all servers connection...")
        k = list(self.servers.keys())
        for srv in k:
            self.servers[srv].disconnect()


def hotswap(bak):
    return Bot(bak.servers, bak.modules, bak.modules_path)

def reload():
    import imp

    import prompt.builtins
    imp.reload(prompt.builtins)

    import event
    imp.reload(event)

    import hooks
    imp.reload(hooks)

    import xmlparser
    imp.reload(xmlparser)
    import xmlparser.node
    imp.reload(xmlparser.node)

    import importer
    imp.reload(importer)

    import server
    imp.reload(server)

    import channel
    imp.reload(channel)

    import DCC
    imp.reload(DCC)

    import message
    imp.reload(message)
