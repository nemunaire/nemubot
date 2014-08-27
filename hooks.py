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

import logging
import re

from response import Response
from exception import IRCException

logger = logging.getLogger("nemubot.hooks")

class MessagesHook:
    def __init__(self, context, bot):
        self.context = context
        self.bot = bot

        # Store specials hooks
        self.all_pre  = list() # Treated before any parse
        self.all_post = list() # Treated before send message to user

        # Store IRC commands hooks
        self.irc_hook = dict()

        # Store direct hooks
        self.cmd_hook = dict()
        self.ask_hook = dict()
        self.msg_hook = dict()

        # Store regexp hooks
        self.cmd_rgxp = list()
        self.ask_rgxp = list()
        self.msg_rgxp = list()

        # Store default hooks (after other hooks if no match)
        self.cmd_default = list()
        self.ask_default = list()
        self.msg_default = list()


    def add_hook(self, store, hook, module_src=None):
        """Insert in the right place a hook into the given store"""
        logger.info("Adding hook '%s' to store '%s' from module '%s'", hook, store, module_src)
        if module_src is None:
            logger.warn("No source module was passed to add_hook function, "
                        "please fix it in order to be compatible with unload "
                        "feature")

        if store in self.context.hooks_cache:
            logger.debug("Cleaning hooks cache for %s", store)
            del self.context.hooks_cache[store]

        if not hasattr(self, store):
            # TODO: raise custom exception, this is a user problem, not internal one!
            logger.error("Unrecognized hook store: %s", store)
            return
        attr = getattr(self, store)

        if isinstance(attr, dict) and hook.name is not None:
            if hook.name not in attr:
                attr[hook.name] = list()
            attr[hook.name].append(hook)
            if hook.end is not None:
                if hook.end not in attr:
                    attr[hook.end] = list()
                attr[hook.end].append(hook)
        elif isinstance(attr, list):
            attr.append(hook)
        else:
            logger.critical("Unrecognized hook store type: %s", type(attr))
            return
        if module_src is not None and hasattr(module_src, "REGISTERED_HOOKS"):
            module_src.REGISTERED_HOOKS.append((store, hook))

    def register_hook_attributes(self, store, module, node):
        if node.hasAttribute("data"):
            data = node["data"]
        else:
            data = None
        if node.hasAttribute("name"):
            self.add_hook(store + "_hook", Hook(getattr(module, node["call"]),
                                                node["name"], data=data),
                          module)
        elif node.hasAttribute("regexp"):
            self.add_hook(store + "_rgxp", Hook(getattr(module, node["call"]),
                                                regexp=node["regexp"], data=data),
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

    def clear(self):
        for h in self.all_pre:
            self.del_hook("all_pre", h)
        for h in self.all_post:
            self.del_hook("all_post", h)

        for l in self.irc_hook:
            for h in self.irc_hook[l]:
                self.del_hook("irc_hook", h)

        for l in self.cmd_hook:
            for h in self.cmd_hook[l]:
                self.del_hook("cmd_hook", h)
        for l in self.ask_hook:
            for h in self.ask_hook[l]:
                self.del_hook("ask_hook", h)
        for l in self.msg_hook:
            for h in self.msg_hook[l]:
                self.del_hook("msg_hook", h)

        for h in self.cmd_rgxp:
            self.del_hook("cmd_rgxp", h)
        for h in self.ask_rgxp:
            self.del_hook("ask_rgxp", h)
        for h in self.msg_rgxp:
            self.del_hook("msg_rgxp", h)

        for h in self.cmd_default:
            self.del_hook("cmd_default", h)
        for h in self.ask_default:
            self.del_hook("ask_default", h)
        for h in self.msg_default:
            self.del_hook("msg_default", h)

    def del_hook(self, store, hook, module_src=None):
        """Remove a registered hook from a given store"""
        if store in self.context.hooks_cache:
            del self.context.hooks_cache[store]

        if not hasattr(self, store):
            logger.warn("unrecognized hook store type")
            return
        attr = getattr(self, store)

        if isinstance(attr, dict) and hook.name is not None:
            if hook.name in attr:
                attr[hook.name].remove(hook)
            if hook.end is not None and hook.end in attr:
                attr[hook.end].remove(hook)
        else:
            attr.remove(hook)

        if module_src is not None:
            module_src.REGISTERED_HOOKS.remove((store, hook))


class Hook:
    """Class storing hook informations"""
    def __init__(self, call, name=None, data=None, regexp=None, channels=list(), server=None, end=None, call_end=None, help=None):
        self.name = name
        self.end = end
        self.call = call
        if call_end is None:
            self.call_end = self.call
        else:
            self.call_end = call_end
        self.regexp = regexp
        self.data = data
        self.times = -1
        self.server = server
        self.channels = channels
        self.help = help

    def is_matching(self, strcmp, channel=None, server=None):
        """Test if the current hook correspond to the message"""
        return (channel is None or len(self.channels) <= 0 or
                channel in self.channels) and (server is None or
             self.server is None or self.server == server) and (
            (self.name is None or strcmp == self.name) and (
            self.end is None or strcmp == self.end) and (
            self.regexp is None or re.match(self.regexp, strcmp)))

    def run(self, msg, data2=None, strcmp=None):
        """Run the hook"""
        if self.times != 0:
            self.times -= 1

        if (self.end is not None and strcmp is not None and
            self.call_end is not None and strcmp == self.end):
            call = self.call_end
            self.times = 0
        else:
            call = self.call

        try:
            if self.data is None:
                if data2 is None:
                    return call(msg)
                elif isinstance(data2, dict):
                    return call(msg, **data2)
                else:
                    return call(msg, data2)
            elif isinstance(self.data, dict):
                if data2 is None:
                    return call(msg, **self.data)
                else:
                    return call(msg, data2, **self.data)
            else:
                if data2 is None:
                    return call(msg, self.data)
                elif isinstance(data2, dict):
                    return call(msg, self.data, **data2)
                else:
                    return call(msg, self.data, data2)
        except IRCException as e:
            return e.fill_response(msg)

last_registered = []

def hook(store, *args, **kargs):
    def sec(call):
        last_registered.append((store, Hook(call, *args, **kargs)))
        return call
    return sec
