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

from datetime import datetime
import threading

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
        self.event_timer = None


    def add_event(self, evt):
        # Add the event in place
        t = evt.current
        i = 0
        for i in range(0, len(self.events)):
            if self.events[i].current > t:
                break
        self.events.insert(i, evt)
        if i == 0:
            self.update_timer()

    def update_timer(self):
        # Reset the timer if this is the first item
        if self.event_timer is not None:
            self.event_timer.cancel()
        if len(self.events) > 0:
            #print ("Update timer, next in", self.events[0].time_left.seconds,
            #       "seconds")
            if datetime.now() >= self.events[0].current:
                self.end_timer()
            else:
                self.event_timer = threading.Timer(
                    self.events[0].time_left.seconds + 1, self.end_timer)
                self.event_timer.start()
        #else:
        #    print ("Update timer: no timer left")


    def end_timer(self):
        #print ("end timer")
        while len(self.events)>0 and datetime.now() >= self.events[0].current:
            #print ("end timer: while")
            evt = self.events.pop(0)
            evt.launch_check()
            if evt.next is not None:
                self.add_event(evt)
        self.update_timer()


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
