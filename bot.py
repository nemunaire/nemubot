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
from queue import Queue
import threading

from consumer import Consumer
import event
import hooks
from networkbot import NetworkBot
from server import Server

ID_letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

class Bot:
    def __init__(self, servers=dict(), modules=dict(), mp=list()):
        # Bot general informations
        self.version     = 3.2
        self.version_txt = "3.2-dev"

        # Keep global context: servers and modules
        self.servers = servers
        self.modules = modules

        # Context paths
        self.modules_path = mp
        self.datas_path   = './datas/'

        # Events
        self.events      = list()
        self.event_timer = None

        # Own hooks
        self.hooks       = hooks.MessagesHook(self)

        # Other known bots, making a bots network
        self.network     = dict()
        self.hooks_cache = dict()

        # Messages to be treated
        self.msg_queue     = Queue()
        self.msg_thrd      = list()
        self.msg_thrd_size = -1


    def add_event(self, evt, eid=None):
        """Register an event and return its identifiant for futur update"""
        if eid is None:
            # Find an ID
            now = datetime.now()
            evt.id = "%d%c%d%d%c%d%d%c%d" % (now.year, ID_letters[now.microsecond % 52],
                                             now.month, now.day, ID_letters[now.microsecond % 42],
                                             now.hour, now.minute, ID_letters[now.microsecond % 32],
                                             now.second)
        else:
            evt.id = eid

        # Add the event in place
        t = evt.current
        i = -1
        for i in range(0, len(self.events)):
            if self.events[i].current > t:
                i -= 1
                break
        self.events.insert(i + 1, evt)
        if i == -1:
            self.update_timer()
            if len(self.events) <= 0 or self.events[i+1] != evt:
                return None

        return evt.id

    def del_event(self, id):
        """Find and remove an event from list"""
        if len(self.events) > 0 and id == self.events[0].id:
            self.events.remove(self.events[0])
            self.update_timer()
            return True

        for evt in self.events:
            if evt.id == id:
                self.events.remove(evt)
                return True
        return False

    def update_timer(self):
        """Relaunch the timer to end with the closest event"""
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
        """Function called at the end of the timer"""
        #print ("end timer")
        while len(self.events)>0 and datetime.now() >= self.events[0].current:
            #print ("end timer: while")
            evt = self.events.pop(0)
            evt.launch_check()
            if evt.next is not None:
                self.add_event(evt, evt.id)
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
                self.modules[name].unload(self)
            # Remove registered hooks
            for (s, h) in self.modules[name].REGISTERED_HOOKS:
                self.hooks.del_hook(s, h)
            # Remove from the dict
            del self.modules[name]
            return True
        return False


    def receive_message(self, srv, raw_msg, private=False, data=None):
        """Queued the message for treatment"""
        self.msg_queue.put_nowait((srv, raw_msg, datetime.now(), private, data))

        # Launch a new thread if necessary
        if self.msg_queue.qsize() > self.msg_thrd_size:
            c = Consumer(self)
            self.msg_thrd.append(c)
            c.start()
            self.msg_thrd_size += 2


    def add_networkbot(self, srv, dest, dcc=None):
        """Append a new bot into the network"""
        id = srv.id + "/" + dest
        if id not in self.network:
            self.network[id] = NetworkBot(self, srv, dest, dcc)
        return self.network[id]


    def quit(self, verb=False):
        """Save and unload modules and disconnect servers"""
        if self.event_timer is not None:
            if verb: print ("Stop the event timer...")
            self.event_timer.cancel()

        if verb: print ("Save and unload all modules...")
        k = list(self.modules.keys())
        for mod in k:
            self.unload_module(mod, verb)

        if verb: print ("Close all servers connection...")
        k = list(self.servers.keys())
        for srv in k:
            self.servers[srv].disconnect()

# Hooks cache

    def create_cache(self, name):
        if name not in self.hooks_cache:
            if isinstance(self.hooks.__dict__[name], list):
                self.hooks_cache[name] = list()

                # Start by adding locals hooks
                for h in self.hooks.__dict__[name]:
                    tpl = (h, 0, self.hooks.__dict__[name])
                    self.hooks_cache[name].append(tpl)

                # Now, add extermal hooks
                level = 0
                while level == 0 or lvl_exist:
                    lvl_exist = False
                    for ext in self.network:
                        if len(self.network[ext].hooks) > level:
                            lvl_exist = True
                            for h in self.network[ext].hooks[level].__dict__[name]:
                                if h not in self.hooks_cache[name]:
                                    self.hooks_cache[name].append((h, level + 1,
                                                                   self.network[ext].hooks[level].__dict__[name]))
                    level += 1

            elif isinstance(self.hooks.__dict__[name], dict):
                self.hooks_cache[name] = dict()

                # Start by adding locals hooks
                for h in self.hooks.__dict__[name]:
                    self.hooks_cache[name][h] = (self.hooks.__dict__[name][h], 0,
                                                 self.hooks.__dict__[name])

                # Now, add extermal hooks
                level = 0
                while level == 0 or lvl_exist:
                    lvl_exist = False
                    for ext in self.network:
                        if len(self.network[ext].hooks) > level:
                            lvl_exist = True
                            for h in self.network[ext].hooks[level].__dict__[name]:
                                if h not in self.hooks_cache[name]:
                                    self.hooks_cache[name][h] = (self.network[ext].hooks[level].__dict__[name][h], level + 1, self.network[ext].hooks[level].__dict__[name])
                    level += 1

            else:
                raise Exception(name + " hook type unrecognized")

        return self.hooks_cache[name]

# Treatment

    def check_rest_times(self, store, hook):
        """Remove from store the hook if it has been executed given time"""
        if hook.times == 0:
            if isinstance(store, dict):
                store[hook.name].remove(hook)
                if len(store) == 0:
                    del store[hook.name]
            elif isinstance(store, list):
                store.remove(hook)

    def treat_pre(self, msg):
        """Treat a message before all other treatment"""
        for h, lvl, store in self.create_cache("all_pre"):
            h.run(msg)
            self.check_rest_times(store, h)


    def treat_cmd(self, msg):
        """Treat a command message"""
        treated = list()

        # First, treat simple hook
        cmd_hook = self.create_cache("cmd_hook")
        if msg.cmd[0] in cmd_hook:
            (hks, lvl, store) = cmd_hook[msg.cmd[0]]
            for h in hks:
                res = h.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(store, h)

        # Then, treat regexp based hook
        cmd_rgxp = self.create_cache("cmd_rgxp")
        for hook, lvl, store in cmd_rgxp:
            if hook.is_matching(msg.cmd[0], msg.channel):
                res = hook.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(store, hook)

        # Finally, treat default hooks if not catched before
        cmd_default = self.create_cache("cmd_default")
        for hook, lvl, store in cmd_default:
            if treated:
                break
            res = hook.run(msg)
            if res is not None and res != False:
                treated.append(res)
            self.check_rest_times(store, hook)

        return treated

    def treat_ask(self, msg):
        """Treat an ask message"""
        treated = list()

        # First, treat simple hook
        ask_hook = self.create_cache("ask_hook")
        if msg.content in ask_hook:
            hks, lvl, store = ask_hook[msg.content]
            for h in hks:
                res = h.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(store, h)

        # Then, treat regexp based hook
        ask_rgxp = self.create_cache("ask_rgxp")
        for hook, lvl, store in ask_rgxp:
            if hook.is_matching(msg.content, msg.channel):
                res = hook.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(store, hook)

        # Finally, treat default hooks if not catched before
        ask_default = self.create_cache("ask_default")
        for hook, lvl, store in ask_default:
            if treated:
                break
            res = hook.run(msg)
            if res is not None and res != False:
                treated.append(res)
            self.check_rest_times(store, hook)

        return treated

    def treat_answer(self, msg):
        """Treat a normal message"""
        treated = list()

        # First, treat simple hook
        msg_hook = self.create_cache("msg_hook")
        if msg.content in msg_hook:
            hks, lvl, store = msg_hook[msg.content]
            for h in hks:
                res = h.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(store, h)

        # Then, treat regexp based hook
        msg_rgxp = self.create_cache("msg_rgxp")
        for hook, lvl, store in msg_rgxp:
            if hook.is_matching(msg.content, msg.channel):
                res = hook.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(store, hook)

        # Finally, treat default hooks if not catched before
        msg_default = self.create_cache("msg_default")
        for hook, lvl, store in msg_default:
            if len(treated) > 0:
                break
            res = hook.run(msg)
            if res is not None and res != False:
                treated.append(res)
            self.check_rest_times(store, hook)

        return treated


def hotswap(bak):
    return Bot(bak.servers, bak.modules, bak.modules_path)

def reload():
    import imp

    import channel
    imp.reload(channel)

    import consumer
    imp.reload(consumer)

    import DCC
    imp.reload(DCC)

    import event
    imp.reload(event)

    import hooks
    imp.reload(hooks)

    import importer
    imp.reload(importer)

    import message
    imp.reload(message)

    import prompt.builtins
    imp.reload(prompt.builtins)

    import server
    imp.reload(server)

    import xmlparser
    imp.reload(xmlparser)
    import xmlparser.node
    imp.reload(xmlparser.node)
