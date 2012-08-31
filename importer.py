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

from importlib.abc import Finder
from importlib.abc import SourceLoader
import imp
import os
import sys

from hooks import Hook
import response
import xmlparser

class ModuleFinder(Finder):
    def __init__(self, context, prompt):
        self.context = context
        self.prompt = prompt

    def find_module(self, fullname, path=None):
        #print ("looking for", fullname, "in", path)
        # Search only for new nemubot modules (packages init)
        if path is None:
            for mpath in self.context.modules_path:
                #print ("looking for", fullname, "in", mpath)
                if os.path.isfile(mpath + fullname + ".xml"):
                    return ModuleLoader(self.context, self.prompt, fullname,
                                        mpath, mpath + fullname + ".xml")
                elif (os.path.isfile(mpath + fullname + ".py") or
                      os.path.isfile(mpath + fullname + "/__init__.py")):
                    return ModuleLoader(self.context, self.prompt,
                                        fullname, mpath, None)
        #print ("not found")
        return None


class ModuleLoader(SourceLoader):
    def __init__(self, context, prompt, fullname, path, config_path):
        self.context = context
        self.prompt = prompt
        self.name = fullname
        self.config_path = config_path

        if config_path is not None:
            self.config = xmlparser.parse_file(config_path)
            if self.config.hasAttribute("name"):
                self.name = self.config["name"]
        else:
            self.config = None

        if os.path.isfile(path + fullname + ".py"):
            self.source_path = path + self.name + ".py"
            self.package = False
        elif os.path.isfile(path + fullname + "/__init__.py"):
            self.source_path = path + self.name + "/__init__.py"
            self.package = True
        else:
            raise ImportError

    def get_filename(self, fullname):
        """Return the path to the source file as found by the finder."""
        return self.source_path

    def get_data(self, path):
        """Return the data from path as raw bytes."""
        with open(path, 'rb') as file:
            return file.read()

    def path_mtime(self, path):
        st = os.stat(path)
        return int(st.st_mtime)

    def set_data(self, path, data):
        """Write bytes data to a file."""
        parent, filename = os.path.split(path)
        path_parts = []
        # Figure out what directories are missing.
        while parent and not os.path.isdir(parent):
            parent, part = os.path.split(parent)
            path_parts.append(part)
        # Create needed directories.
        for part in reversed(path_parts):
            parent = os.path.join(parent, part)
            try:
                os.mkdir(parent)
            except FileExistsError:
                # Probably another Python process already created the dir.
                continue
            except PermissionError:
                # If can't get proper access, then just forget about writing
                # the data.
                return
        try:
            with open(path, 'wb') as file:
                file.write(data)
        except (PermissionError, FileExistsError):
            pass

    def get_code(self, fullname):
        return SourceLoader.get_code(self, fullname)

    def get_source(self, fullname):
        return SourceLoader.get_source(self, fullname)

    def is_package(self, fullname):
        return self.package

    def load_module(self, fullname):
        module = self._load_module(fullname, sourceless=True)

        # Remove the module from sys list
        del sys.modules[fullname]

        # If the module was already loaded, then reload it
        if hasattr(module, '__LOADED__'):
            reload(module)

        # Check that is a valid nemubot module
        if not hasattr(module, "nemubotversion"):
            raise ImportError("Module `%s' is not a nemubot module."%self.name)
        # Check module version
        if module.nemubotversion != self.context.version:
            raise ImportError("Module `%s' is not compatible with this "
                              "version." % self.name)

        # Set module common functions and datas
        module.__LOADED__ = True

        # Set module common functions and datas
        module.DEBUG = False
        module.name = fullname
        module.print = lambda msg: print("[%s] %s"%(module.name, msg))
        module.print_debug = lambda msg: mod_print_dbg(module, msg)

        if not hasattr(module, "NODATA"):
            module.DATAS = xmlparser.parse_file(self.context.datas_path
                                                + module.name + ".xml")
            module.save = lambda: mod_save(module, self.context.datas_path)
        else:
            module.DATAS = None
            module.save = lambda: False
        module.CONF = self.config
        module.has_access = lambda msg: mod_has_access(module,
                                                       module.CONF, msg)

        module.ModuleState = xmlparser.module_state.ModuleState
        module.Response = response.Response

        # Load dependancies
        if module.CONF is not None and module.CONF.hasNode("dependson"):
            module.MODS = dict()
            for depend in module.CONF.getNodes("dependson"):
                for md in MODS:
                    if md.name == depend["name"]:
                        mod.MODS[md.name] = md
                        break
                if depend["name"] not in module.MODS:
                    print ("\033[1;31mERROR:\033[0m in module `%s', module "
                           "`%s' require by this module but is not loaded."
                           % (module.name, depend["name"]))
                    return

        # Add the module to the global modules list
        if self.context.add_module(module):

            # Launch the module
            if hasattr(module, "load"):
                module.load(self.context)

            # Register hooks
            register_hooks(module, self.context, self.prompt)

            print ("  Module `%s' successfully loaded." % module.name)
        else:
            raise ImportError("An error occurs while importing `%s'."
                              % module.name)
        return module


def add_cap_hook(prompt, module, cmd):
    if hasattr(module, cmd["call"]):
        prompt.add_cap_hook(cmd["name"], getattr(module, cmd["call"]))
    else:
        print ("Warning: In module `%s', no function `%s' defined for `%s' "
               "command hook." % (module.name, cmd["call"], cmd["name"]))

def register_hooks(module, context, prompt):
    """Register all available hooks"""
    if module.CONF is not None:
        # Register command hooks
        if module.CONF.hasNode("command"):
            for cmd in module.CONF.getNodes("command"):
                if cmd.hasAttribute("name") and cmd.hasAttribute("call"):
                    add_cap_hook(prompt, module, cmd)

        # Register message hooks
        if module.CONF.hasNode("message"):
            for msg in module.CONF.getNodes("message"):
                context.hooks.register_hook(module, msg)

    # Register legacy hooks
    if hasattr(module, "parseanswer"):
        context.hooks.add_hook("cmd_default", Hook(module.parseanswer))
    if hasattr(module, "parseask"):
        context.hooks.add_hook("ask_default", Hook(module.parseask))
    if hasattr(module, "parselisten"):
        context.hooks.add_hook("msg_default", Hook(module.parselisten))

##########################
#                        #
#    Module functions    #
#                        #
##########################

def mod_print_dbg(mod, msg):
    if mod.DEBUG:
        print("{%s} %s"%(mod.name, msg))

def mod_save(mod, datas_path):
    mod.DATAS.save(datas_path + "/" + mod.name + ".xml")
    mod.print ("Saving!")

def mod_has_access(mod, config, msg):
    if config is not None and config.hasNode("channel"):
        for chan in config.getNodes("channel"):
            if (chan["server"] is None or chan["server"] == msg.srv.id) and (
                chan["channel"] is None or chan["channel"] == msg.channel):
                return True
        return False
    else:
        return True
