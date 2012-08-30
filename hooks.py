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

from response import Response

class MessagesHook:
    def __init__(self):
        # Store specials hook
        self.all_pre  = list() # Treated before any parse
        #self.all_post = list() # Treated before send message to user

        # Store direct hook
        self.cmd_hook = dict()
        self.ask_hook = dict()
        self.msg_hook = dict()

        # Store regexp hook
        self.cmd_rgxp = list()
        self.ask_rgxp = list()
        self.msg_rgxp = list()

        # Store default hooks (after other hooks if no match)
        self.cmd_default = list()
        self.ask_default = list()
        self.msg_default = list()


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

    def register_hook_attributes(self, store, module, node):
        if node.hasAttribute("name"):
            self.add_hook(getattr(self, store + "_hook"), Hook(getattr(module,
                                              node["call"]),
                                      node["name"]))
        elif node.hasAttribute("regexp"):
            self.add_hook(getattr(self, store + "_rgxp"), Hook(getattr(module,
                                              node["call"]),
                                      None, None,
                                      node["regexp"]))

    def register_hook(self, module, node):
        """Create a hook from configuration node"""
        if node.name == "message" and node.hasAttribute("type"):
            if node["type"] == "cmd" or node["type"] == "all":
                self.register_hook_attributes("cmd", module, node)

            if node["type"] == "ask" or node["type"] == "all":
                self.register_hook_attributes("ask", module, node)

            if (node["type"] == "msg" or node["type"] == "answer" or
                node["type"] == "all"):
                self.register_hook_attributes("answer", module, node)

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
        for h in self.all_pre:
            h.run(msg)
            self.check_rest_times(self.all_pre, h)


    def treat_cmd(self, msg):
        """Treat a command message"""
        treated = list()

        # First, treat simple hook
        if msg.cmd[0] in self.cmd_hook:
            for h in self.cmd_hook[msg.cmd[0]]:
                res = h.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(self.cmd_hook, h)

        # Then, treat regexp based hook
        for hook in self.cmd_rgxp:
            if hook.is_matching(msg.cmd[0], msg.channel):
                res = hook.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(self.cmd_rgxp, hook)

        # Finally, treat default hooks if not catched before
        for hook in self.cmd_default:
            if treated:
                break
            res = hook.run(msg)
            if res is not None and res != False:
                treated.append(res)
            self.check_rest_times(self.cmd_default, hook)

        return treated

    def treat_ask(self, msg):
        """Treat an ask message"""
        treated = list()

        # First, treat simple hook
        if msg.content in self.ask_hook:
            for h in self.ask_hook[msg.content]:
                res = h.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(self.ask_hook, h)

        # Then, treat regexp based hook
        for hook in self.ask_rgxp:
            if hook.is_matching(msg.content, msg.channel):
                res = hook.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(self.ask_rgxp, hook)

        # Finally, treat default hooks if not catched before
        for hook in self.ask_default:
            if treated:
                break
            res = hook.run(msg)
            if res is not None and res != False:
                treated.append(res)
            self.check_rest_times(self.ask_default, hook)

        return treated

    def treat_answer(self, msg):
        """Treat a normal message"""
        treated = list()

        # First, treat simple hook
        if msg.content in self.msg_hook:
            for h in self.msg_hook[msg.content]:
                res = h.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(self.msg_hook, h)

        # Then, treat regexp based hook
        for hook in self.msg_rgxp:
            if hook.is_matching(msg.content, msg.channel):
                res = hook.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(self.msg_rgxp, hook)

        # Finally, treat default hooks if not catched before
        for hook in self.msg_default:
            if len(treated) > 0:
                break
            res = hook.run(msg)
            if res is not None and res != False:
                treated.append(res)
            self.check_rest_times(self.msg_default, hook)

        return treated


class Hook:
    """Class storing hook informations"""
    def __init__(self, call, name=None, data=None, regexp=None, channels=list()):
        self.name = name
        self.call = call
        self.regexp = regexp
        self.data = data
        self.times = -1
        self.channels = channels

    def is_matching(self, strcmp, channel):
        """Test if the current hook correspond to the message"""
        return (len(self.channel) <= 0 or channel in self.channels) and (
            (self.name is not None and strcmp == self.name) or (
            self.regexp is not None and re.match(self.regexp, strcmp)))

    def run(self, msg):
        """Run the hook"""
        if self.times != 0:
            self.times -= 1

        if self.data is None:
            return self.call(msg)
        elif isinstance(self.data, dict):
            return self.call(msg, **self.data)
        else:
            return self.call(msg, self.data)
