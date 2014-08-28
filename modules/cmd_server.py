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

import traceback
import sys

from networkbot import NetworkBot
from hooks import hook

nemubotversion = 3.4
NODATA = True

def getserver(toks, context, prompt):
    """Choose the server in toks or prompt"""
    if len(toks) > 1 and toks[0] in context.servers:
        return (context.servers[toks[0]], toks[1:])
    elif prompt.selectedServer is not None:
        return (prompt.selectedServer, toks)
    else:
        return (None, toks)

@hook("prompt_cmd", "close")
def close(data, toks, context, prompt):
    """Disconnect and forget (remove from the servers list) the server"""
    if len(toks) > 1:
        for s in toks[1:]:
            if s in servers:
                context.servers[s].disconnect()
                del context.servers[s]
            else:
                print ("close: server `%s' not found." % s)
    elif prompt.selectedServer is not None:
        prompt.selectedServer.disconnect()
        del prompt.servers[selectedServer.id]
        prompt.selectedServer = None
    return

@hook("prompt_cmd", "connect")
def connect(data, toks, context, prompt):
    """Make the connexion to a server"""
    if len(toks) > 1:
        for s in toks[1:]:
            if s in context.servers:
                context.servers[s].launch(context.receive_message)
            else:
                print ("connect: server `%s' not found." % s)

    elif prompt.selectedServer is not None:
        prompt.selectedServer.launch(context.receive_message)
    else:
        print ("  Please SELECT a server or give its name in argument.")

@hook("prompt_cmd", "disconnect")
def disconnect(data, toks, context, prompt):
    """Close the connection to a server"""
    if len(toks) > 1:
        for s in toks[1:]:
            if s in context.servers:
                if not context.servers[s].disconnect():
                    print ("disconnect: server `%s' already disconnected." % s)
            else:
                print ("disconnect: server `%s' not found." % s)
    elif prompt.selectedServer is not None:
        if not prompt.selectedServer.disconnect():
            print ("disconnect: server `%s' already disconnected."
                   % prompt.selectedServer.id)
    else:
        print ("  Please SELECT a server or give its name in argument.")

@hook("prompt_cmd", "discover")
def discover(data, toks, context, prompt):
    """Discover a new bot on a server"""
    (srv, toks) = getserver(toks, context, prompt)
    if srv is not None:
        for name in toks[1:]:
            if "!" in name:
                bot = context.add_networkbot(srv, name)
                bot.connect()
            else:
                print ("  %s is not a valid fullname, for example: nemubot!nemubotV3@bot.nemunai.re")
    else:
        print ("  Please SELECT a server or give its name in first argument.")

@hook("prompt_cmd", "hotswap")
def hotswap(data, toks, context, prompt):
    """Reload a server class"""
    if len(toks) > 1:
        print ("hotswap: apply only on selected server")
    elif prompt.selectedServer is not None:
        del context.servers[prompt.selectedServer.id]
        srv = server.Server(selectedServer.node, selectedServer.nick,
                            selectedServer.owner, selectedServer.realname,
                            selectedServer.s)
        context.servers[srv.id] = srv
        prompt.selectedServer.kill()
        prompt.selectedServer = srv
        prompt.selectedServer.start()
    else:
        print ("  Please SELECT a server or give its name in argument.")

@hook("prompt_cmd", "join")
def join(data, toks, context, prompt):
    """Join or leave a channel"""
    rd = 1
    if len(toks) <= rd:
        print ("%s: not enough arguments." % toks[0])
        return

    if toks[rd] in context.servers:
        srv = context.servers[toks[rd]]
        rd += 1
    elif prompt.selectedServer is not None:
        srv = prompt.selectedServer
    else:
        print ("  Please SELECT a server or give its name in argument.")
        return

    if len(toks) <= rd:
        print ("%s: not enough arguments."  % toks[0])
        return

    if toks[0] == "join":
        if len(toks) > rd + 1:
            srv.join(toks[rd], toks[rd + 1])
        else:
            srv.join(toks[rd])
    elif toks[0] == "leave" or toks[0] == "part":
        srv.leave(toks[rd])
    return

@hook("prompt_cmd", "save")
def save_mod(data, toks, context, prompt):
    """Force save module data"""
    if len(toks) < 2:
        print ("save: not enough arguments.")
        return

    for mod in toks[1:]:
        if mod in context.modules:
            context.modules[mod].save()
            print ("save: module `%s´ saved successfully" % mod)
        else:
            print ("save: no module named `%s´" % mod)
    return

@hook("prompt_cmd", "send")
def send(data, toks, context, prompt):
    """Send a message on a channel"""
    rd = 1
    if len(toks) <= rd:
        print ("send: not enough arguments.")
        return

    if toks[rd] in context.servers:
        srv = context.servers[toks[rd]]
        rd += 1
    elif prompt.selectedServer is not None:
        srv = prompt.selectedServer
    else:
        print ("  Please SELECT a server or give its name in argument.")
        return

    if len(toks) <= rd:
        print ("send: not enough arguments.")
        return

    #Check the server is connected
    if not srv.connected:
        print ("send: server `%s' not connected." % srv.id)
        return

    if toks[rd] in srv.channels:
        chan = toks[rd]
        rd += 1
    else:
        print ("send: channel `%s' not authorized in server `%s'."
               % (toks[rd], srv.id))
        return

    if len(toks) <= rd:
        print ("send: not enough arguments.")
        return

    srv.send_msg_final(chan, toks[rd])
    return "done"

@hook("prompt_cmd", "zap")
def zap(data, toks, context, prompt):
    """Hard change connexion state"""
    if len(toks) > 1:
        for s in toks[1:]:
            if s in context.servers:
                context.servers[s].connected = not context.servers[s].connected
            else:
                print ("zap: server `%s' not found." % s)
    elif prompt.selectedServer is not None:
        prompt.selectedServer.connected = not prompt.selectedServer.connected
    else:
        print ("  Please SELECT a server or give its name in argument.")

@hook("prompt_cmd", "top")
def top(data, toks, context, prompt):
    """Display consumers load information"""
    print("Queue size: %d, %d thread(s) running (counter: %d)" % (context.cnsr_queue.qsize(), len(context.cnsr_thrd), context.cnsr_thrd_size))
    if len(context.events) > 0:
        print("Events registered: %d, next in %d seconds" % (len(context.events), context.events[0].time_left.seconds))
    else:
        print("No events registered")

    for th in context.cnsr_thrd:
        if th.is_alive():
            print("################ Stack trace for thread %u ################" % th.ident)
            traceback.print_stack(sys._current_frames()[th.ident])

@hook("prompt_cmd", "netstat")
def netstat(data, toks, context, prompt):
    """Display sockets in use and many other things"""
    if len(context.network) > 0:
        print("Distant bots connected: %d:" % len(context.network))
        for name, bot in context.network.items():
            print("# %s:" % name)
            print("  * Declared hooks:")
            lvl = 0
            for hlvl in bot.hooks:
                lvl += 1
                for hook in hlvl.all_pre + hlvl.all_post + hlvl.cmd_rgxp + hlvl.cmd_default + hlvl.ask_rgxp + hlvl.ask_default + hlvl.msg_rgxp + hlvl.msg_default:
                    print("  %s- %s" % (' ' * lvl * 2, hook))
                for kind in [ "irc_hook", "cmd_hook", "ask_hook", "msg_hook" ]:
                    print("  %s- <%s> %s" % (' ' * lvl * 2, kind, ", ".join(hlvl.__dict__[kind].keys())))
            print("  * My tag: %d" % bot.my_tag)
            print("  * Tags in use (%d):" % bot.inc_tag)
            for tag, (cmd, data) in bot.tags.items():
                print("    - %11s: %s « %s »" % (tag, cmd, data))
    else:
        print("No distant bot connected")
