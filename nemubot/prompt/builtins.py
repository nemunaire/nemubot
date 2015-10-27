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

def end(toks, context, prompt):
    """Quit the prompt for reload or exit"""
    from nemubot.prompt.reset import PromptReset

    if toks[0] == "refresh":
        raise PromptReset("refresh")
    elif toks[0] == "reset":
        raise PromptReset("reset")
    raise PromptReset("quit")


def liste(toks, context, prompt):
    """Show some lists"""
    if len(toks) > 1:
        for l in toks[1:]:
            l = l.lower()
            if l == "server" or l == "servers":
                for srv in context.servers.keys():
                    print ("  - %s (state: %s) ;" % (srv,
                                                     "connected" if context.servers[srv].connected else "disconnected"))
                if len(context.servers) == 0:
                    print ("  > No server loaded")

            elif l == "mod" or l == "mods" or l == "module" or l == "modules":
                for mod in context.modules.keys():
                    print ("  - %s ;" % mod)
                if len(context.modules) == 0:
                    print ("  > No module loaded")

            elif l in prompt.HOOKS_LIST:
                f, d = prompt.HOOKS_LIST[l]
                f(d, context, prompt)

            else:
                print ("  Unknown list `%s'" % l)
                return 2
        return 0
    else:
        print ("  Please give a list to show: servers, ...")
        return 1


def load(toks, context, prompt):
    """Load an XML configuration file"""
    if len(toks) > 1:
        for filename in toks[1:]:
            context.load_file(filename)
    else:
        print ("Not enough arguments. `load' takes a filename.")
        return 1


def select(toks, context, prompt):
    """Select the current server"""
    if (len(toks) == 2 and toks[1] != "None" and
        toks[1] != "nemubot" and toks[1] != "none"):
        if toks[1] in context.servers:
            prompt.selectedServer = context.servers[toks[1]]
        else:
            print ("select: server `%s' not found." % toks[1])
            return 1
    else:
        prompt.selectedServer = None


def unload(toks, context, prompt):
    """Unload a module"""
    if len(toks) == 2 and toks[1] == "all":
        for name in context.modules.keys():
            context.unload_module(name)
    elif len(toks) > 1:
        for name in toks[1:]:
            if context.unload_module(name):
                print ("  Module `%s' successfully unloaded." % name)
            else:
                print ("  No module `%s' loaded, can't unload!" % name)
                return 2
    else:
        print ("Not enough arguments. `unload' takes a module name.")
        return 1


def debug(toks, context, prompt):
    """Enable/Disable debug mode on a module"""
    if len(toks) > 1:
        for name in toks[1:]:
            if name in context.modules:
                context.modules[name].DEBUG = not context.modules[name].DEBUG
                if context.modules[name].DEBUG:
                    print ("  Module `%s' now in DEBUG mode." % name)
                else:
                    print ("  Debug for module module `%s' disabled." % name)
            else:
                print ("  No module `%s' loaded, can't debug!" % name)
                return 2
    else:
        print ("Not enough arguments. `debug' takes a module name.")
        return 1


# Register build-ins
CAPS = {
    'quit': end,       # Disconnect all server and quit
    'exit': end,       # Alias for quit
    'reset': end,      # Reload the prompt
    'refresh': end,    # Reload the prompt but save modules
    'load': load,      # Load a servers or module configuration file
    'unload': unload,  # Unload a module and remove it from the list
    'select': select,  # Select a server
    'list': liste,     # Show lists
    'debug': debug,    # Pass a module in debug mode
}
