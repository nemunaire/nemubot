# -*- coding: utf-8 -*-

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

from distutils.version import LooseVersion
from importlib.abc import Finder
from importlib.machinery import SourceFileLoader
import imp
import logging
import os
import sys

from nemubot import __version__
from nemubot.event import ModuleEvent
from nemubot.exception import IRCException
import nemubot.hooks
from nemubot.message import TextMessage
from nemubot.tools.xmlparser import parse_file, module_state

logger = logging.getLogger("nemubot.importer")


class ModuleFinder(Finder):

    def __init__(self, context, prompt):
        self.context = context
        self.prompt = prompt

    def find_module(self, fullname, path=None):
        # print ("looking for", fullname, "in", path)
        # Search only for new nemubot modules (packages init)
        if path is None:
            for mpath in self.context.modules_paths:
                # print ("looking for", fullname, "in", mpath)
                if os.path.isfile(os.path.join(mpath, fullname + ".py")):
                    return ModuleLoader(self.context, self.prompt, fullname,
                                        os.path.join(mpath, fullname + ".py"))
                elif os.path.isfile(os.path.join(os.path.join(mpath, fullname), "__init__.py")):
                    return ModuleLoader(self.context, self.prompt, fullname,
                                        os.path.join(
                                            os.path.join(mpath, fullname),
                                            "__init__.py"))
        # print ("not found")
        return None


class ModuleLoader(SourceFileLoader):

    def __init__(self, context, prompt, fullname, path):
        self.context = context
        self.prompt = prompt

        if fullname in self.context.modules_configuration:
            self.config = self.context.modules_configuration[fullname]
        else:
            self.config = None

        SourceFileLoader.__init__(self, fullname, path)


    def load_module(self, fullname):
        module = SourceFileLoader.load_module(self, fullname)

        # Check that is a valid nemubot module
        if not hasattr(module, "nemubotversion"):
            raise ImportError("Module `%s' is not a nemubot module." %
                              fullname)
        # Check module version
        if LooseVersion(__version__) < LooseVersion(str(module.nemubotversion)):
            raise ImportError("Module `%s' is not compatible with this "
                              "version." % fullname)

        # Set module common functions and data
        module.__LOADED__ = True
        module.logger = logging.getLogger("nemubot.module." + fullname)

        def prnt(*args):
            print("[%s]" % module.__name__, *args)
            module.logger.info(*args)
        def prnt_dbg(*args):
            if module.DEBUG:
                print("{%s}" % module.__name__, *args)
            module.logger.debug(*args)

        def mod_save():
            fpath = os.path.join(self.context.data_path, module.__name__ + ".xml")
            module.print_debug("Saving DATAS to " + fpath)
            module.DATAS.save(fpath)

        def send_response(server, res):
            if server in self.context.servers:
                r = res.next_response()
                if r.server is not None:
                    return self.context.servers[r.server].send_response(r)
                else:
                    return self.context.servers[server].send_response(r)
            else:
                module.logger.error("Try to send a message to the unknown server: %s", server)
                return False

        def add_hook(store, hook):
            store = convert_legacy_store(store)
            module.REGISTERED_HOOKS.append((store, hook))
            return self.context.hooks.add_hook(hook, store)
        def del_hook(store, hook):
            store = convert_legacy_store(store)
            module.REGISTERED_HOOKS.remove((store, hook))
            return self.context.hooks.del_hook(hook, store)
        def add_event(evt, eid=None):
            return self.context.add_event(evt, eid, module_src=module)
        def add_event_eid(evt, eid):
            return add_event(evt, eid)
        def del_event(evt):
            return self.context.del_event(evt, module_src=module)

        # Set module common functions and datas
        module.REGISTERED_HOOKS = list()
        module.REGISTERED_EVENTS = list()
        module.DEBUG = self.context.verbosity > 0
        module.print = prnt
        module.print_debug = prnt_dbg
        module.send_response = send_response
        module.add_hook = add_hook
        module.del_hook = del_hook
        module.add_event = add_event
        module.add_event_eid = add_event_eid
        module.del_event = del_event

        if not hasattr(module, "NODATA"):
            data_file = os.path.join(self.context.data_path,
                                     module.__name__ + ".xml")
            if os.path.isfile(data_file):
                module.DATAS = parse_file(data_file)
            else:
                module.DATAS = module_state.ModuleState("nemubotstate")
            module.save = mod_save
        else:
            module.DATAS = None
            module.save = lambda: False
        module.CONF = self.config

        module.ModuleEvent = ModuleEvent
        module.ModuleState = module_state.ModuleState
        module.IRCException = IRCException

        # Load dependancies
        if module.CONF is not None and module.CONF.hasNode("dependson"):
            module.MODS = dict()
            for depend in module.CONF.getNodes("dependson"):
                for md in MODS:
                    if md.name == depend["name"]:
                        mod.MODS[md.name] = md
                        break
                if depend["name"] not in module.MODS:
                    logger.error("In module `%s', module `%s' require by this "
                                 "module but is not loaded.", module.__name__,
                                                              depend["name"])
                    return

        # Add the module to the global modules list
        if self.context.add_module(module):

            # Launch the module
            if hasattr(module, "load"):
                module.load(self.context)

            # Register hooks
            register_hooks(module, self.context, self.prompt)

            logger.info("Module '%s' successfully loaded.", module.__name__)
        else:
            logger.error("An error occurs while importing `%s'.", module.__name__)
            raise ImportError("An error occurs while importing `%s'."
                              % module.__name__)
        return module


def convert_legacy_store(old):
    if old == "cmd_hook" or old == "cmd_rgxp" or old == "cmd_default":
        return "in_Command"
    elif old == "ask_hook" or old == "ask_rgxp" or old == "ask_default":
        return "in_DirectAsk"
    elif old == "msg_hook" or old == "msg_rgxp" or old == "msg_default":
        return "in_TextMessage"
    elif old == "all_post":
        return "post"
    elif old == "all_pre":
        return "pre"
    else:
        print("UNKNOWN store:", old)
        return old


def register_hooks(module, context, prompt):
    """Register all available hooks

    Arguments:
    module -- the loaded Python module
    context -- bot context
    prompt -- the current Prompt instance
    """

    # Register decorated functions
    for s, h in nemubot.hooks.last_registered:
        if s == "prompt_cmd":
            prompt.add_cap_hook(h.name, h.call)
        elif s == "prompt_list":
            prompt.add_list_hook(h.name, h.call)
        else:
            s = convert_legacy_store(s)
            module.REGISTERED_HOOKS.append((s, h))
            context.hooks.add_hook(h, s)
    nemubot.hooks.last_registered = []
