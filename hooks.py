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
    def __init__(self, context):
        self.context = context

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


    def add_hook(self, store, hook, module_src=None):
        """Insert in the right place a hook into the given store"""
        if module_src is None:
            print ("\033[1;35mWarning:\033[0m No source module was passed to "
                   "add_hook function, please fix it in order to be "
                   "compatible with unload feature")

        if store in self.context.hooks_cache:
            del self.context.hooks_cache[store]

        if not hasattr(self, store):
            print ("\033[1;35mWarning:\033[0m unrecognized hook store")
            return
        attr = getattr(self, store)

        if isinstance(attr, dict) and hook.name is not None:
            if hook.name not in attr:
                attr[hook.name] = list()
            attr[hook.name].append(hook)
        elif isinstance(attr, list):
            attr.append(hook)
        else:
            print ("\033[1;32mWarning:\033[0m unrecognized hook store type")
            return
        if module_src is not None:
            module_src.REGISTERED_HOOKS.append((store, hook))

    def register_hook_attributes(self, store, module, node):
        if node.hasAttribute("name"):
            self.add_hook(store + "_hook", Hook(getattr(module, node["call"]),
                                                node["name"]),
                          module)
        elif node.hasAttribute("regexp"):
            self.add_hook(store + "_rgxp", Hook(getattr(module, node["call"]),
                                                None, None, node["regexp"]),
                          module)

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

    def del_hook(self, store, hook):
        """Remove a registered hook from a given store"""
        if store in self.context.hooks_cache:
            del self.context.hooks_cache[store]

        if not hasattr(self, store):
            print ("Warning: unrecognized hook store type")
            return
        attr = getattr(self, store)

        if isinstance(attr, dict) and hook.name is not None:
            if hook.name in attr:
                attr[hook.name].remove(hook)
        else:
            attr.remove(hook)

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
