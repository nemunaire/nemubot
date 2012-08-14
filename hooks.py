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

class MessagesHook:
    def __init__(self):
        # Store direct hook
        self.cmd_hook = dict()
        self.ask_hook = dict()
        self.msg_hook = dict()

        # Store regexp hook
        self.cmd_rgxp = list()
        self.ask_rgxp = list()
        self.msg_rgxp = list()


    def add_hook(self, store, hook):
        """Insert in the right place a hook into the given store"""
        if isinstance(store, dict) and hook.name is not None:
            if hook.name not in store:
                store[hook.name] = list()
            store[hook.name].append(hook)
        elif isinstance(store, list):
            store.append(hook)
        else:
            print ("Warning: unrecognized hook store type")

    def register_hook(self, module, node):
        """Create a hook from configuration node"""
        if node.name == "message" and node.hasAttribute("type"):
            if node["type"] == "cmd" or node["type"] == "all":
                if node.hasAttribute("name"):
                    self.add_hook(self.cmd_hook, Hook(getattr(module,
                                                              node["call"]),
                                                      node["name"]))
                elif node.hasAttribute("regexp"):
                    self.add_hook(self.cmd_rgxp, Hook(getattr(module,
                                                              node["call"]),
                                                      None, None,
                                                      node["regexp"]))

            if node["type"] == "ask" or node["type"] == "all":
                if node.hasAttribute("name"):
                    self.add_hook(self.ask_hook, Hook(getattr(module,
                                                              node["call"]),
                                                      node["name"]))
                elif node.hasAttribute("regexp"):
                    self.add_hook(self.ask_rgxp, Hook(getattr(module,
                                                              node["call"]),
                                                      None, None,
                                                      node["regexp"]))

            if node["type"] == "answer" or node["type"] == "all":
                if node.hasAttribute("name"):
                    self.add_hook(self.msg_hook, Hook(getattr(module,
                                                              node["call"]),
                                                      node["name"]))
                elif node.hasAttribute("regexp"):
                    self.add_hook(self.msg_rgxp, Hook(getattr(module,
                                                              node["call"]),
                                                      None, None,
                                                      node["regexp"]))


    def check_rest_times(self, store, hook):
        """Remove from store the hook if it has been executed given time"""
        if hook.times == 0:
            if isinstance(store, dict):
                store[hook.name].remove(hook)
                if len(store) == 0:
                    del store[hook.name]
            elif isinstance(store, list):
                store.remove(hook)

    def treat_cmd(self, msg):
        """Treat a command message"""
        # First, treat simple hook
        if msg.cmd[0] in self.cmd_hook:
            for h in self.cmd_hook[msg.cmd[0]]:
                h.run(msg)
                self.check_rest_times(self.cmd_hook, h)

        # Then, treat regexp based hook
        for hook in self.cmd_rgxp:
            if hook.is_matching(msg):
                hook.run(msg)
                self.check_rest_times(self.cmd_rgxp, hook)

    def treat_ask(self, msg):
        """Treat an ask message"""
        # First, treat simple hook
        if msg.content in self.ask_hook:
            for h in self.ask_hook[msg.content]:
                h.run(msg)
                self.check_rest_times(self.ask_hook, h)

        # Then, treat regexp based hook
        for hook in self.ask_rgxp:
            if hook.is_matching(msg):
                hook.run(msg)
                self.check_rest_times(self.ask_rgxp, hook)

    def treat_answer(self, msg):
        """Treat a normal message"""
        # First, treat simple hook
        if msg.content in self.msg_hook:
            for h in self.msg_hook[msg.cmd[0]]:
                h.run(msg)
                self.check_rest_times(self.msg_hook, h)

        # Then, treat regexp based hook
        for hook in self.msg_rgxp:
            if hook.is_matching(msg):
                hook.run(msg)
                self.check_rest_times(self.msg_rgxp, hook)


class Hook:
    """Class storing hook informations"""
    def __init__(self, call, name=None, data=None, regexp=None):
        self.name = name
        self.call = call
        self.regexp = regexp
        self.data = data
        self.times = -1

    def is_matching(self, strcmp):
        """Test if the current hook correspond to the message"""
        return (self.name is not None and strcmp == self.name) or (
            self.regexp is not None and re.match(self.regexp, strcmp))

    def run(self, msg):
        """Run the hook"""
        if self.times > 0:
            self.times -= 1
        return self.call(self.data, msg)
