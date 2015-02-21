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

import traceback
import sys

from nemubot.hooks import hook

nemubotversion = 3.4
NODATA = True


def getserver(toks, context, prompt, mandatory=False, **kwargs):
    """Choose the server in toks or prompt.
    This function modify the tokens list passed as argument"""

    if len(toks) > 1 and toks[1] in context.servers:
        return context.servers[toks.pop(1)]
    elif not mandatory or prompt.selectedServer:
        return prompt.selectedServer
    else:
        from nemubot.prompt.error import PromptError
        raise PromptError("Please SELECT a server or give its name in argument.")


@hook("prompt_cmd", "close")
def close(toks, context, **kwargs):
    """Disconnect and forget (remove from the servers list) the server"""
    srv = getserver(toks, context=context, mandatory=True, **kwargs)

    if srv.close():
        del context.servers[srv.id]
        return 0
    return 1


@hook("prompt_cmd", "connect")
def connect(toks, **kwargs):
    """Make the connexion to a server"""
    srv = getserver(toks, mandatory=True, **kwargs)

    return not srv.open()


@hook("prompt_cmd", "disconnect")
def disconnect(toks, **kwargs):
    """Close the connection to a server"""
    srv = getserver(toks, mandatory=True, **kwargs)

    return not srv.close()


@hook("prompt_cmd", "discover")
def discover(toks, context, **kwargs):
    """Discover a new bot on a server"""
    srv = getserver(toks, context=context, mandatory=True, **kwargs)

    if len(toks) > 1 and "!" in toks[1]:
        bot = context.add_networkbot(srv, name)
        return not bot.connect()
    else:
        print("  %s is not a valid fullname, for example: "
              "nemubot!nemubotV3@bot.nemunai.re" % ''.join(toks[1:1]))
        return 1


@hook("prompt_cmd", "join")
@hook("prompt_cmd", "leave")
@hook("prompt_cmd", "part")
def join(toks, **kwargs):
    """Join or leave a channel"""
    srv = getserver(toks, mandatory=True, **kwargs)

    if len(toks) <= 2:
        print("%s: not enough arguments." % toks[0])
        return 1

    if toks[0] == "join":
        if len(toks) > 2:
            srv.write("JOIN %s %s" % (toks[1], toks[2]))
        else:
            srv.write("JOIN %s" % toks[1])

    elif toks[0] == "leave" or toks[0] == "part":
        if len(toks) > 2:
            srv.write("PART %s :%s" % (toks[1], " ".join(toks[2:])))
        else:
            srv.write("PART %s" % toks[1])

    return 0


@hook("prompt_cmd", "save")
def save_mod(toks, context, **kwargs):
    """Force save module data"""
    if len(toks) < 2:
        print("save: not enough arguments.")
        return 1

    wrn = 0
    for mod in toks[1:]:
        if mod in context.modules:
            context.modules[mod].save()
            print("save: module `%s´ saved successfully" % mod)
        else:
            wrn += 1
            print("save: no module named `%s´" % mod)
    return wrn


@hook("prompt_cmd", "send")
def send(toks, **kwargs):
    """Send a message on a channel"""
    srv = getserver(toks, mandatory=True, **kwargs)

    # Check the server is connected
    if not srv.connected:
        print ("send: server `%s' not connected." % srv.id)
        return 2

    if len(toks) <= 3:
        print ("send: not enough arguments.")
        return 1

    if toks[1] not in srv.channels:
        print ("send: channel `%s' not authorized in server `%s'."
               % (toks[1], srv.id))
        return 3

    from nemubot.message import TextMessage
    srv.send_response(TextMessage(" ".join(toks[2:]), server=None,
                                  to=[toks[1]]))
    return 0


@hook("prompt_cmd", "zap")
def zap(toks, **kwargs):
    """Hard change connexion state"""
    srv = getserver(toks, mandatory=True, **kwargs)

    srv.connected = not srv.connected


@hook("prompt_cmd", "top")
def top(toks, context, **kwargs):
    """Display consumers load information"""
    print("Queue size: %d, %d thread(s) running (counter: %d)" %
          (context.cnsr_queue.qsize(),
           len(context.cnsr_thrd),
           context.cnsr_thrd_size))
    if len(context.events) > 0:
        print("Events registered: %d, next in %d seconds" %
              (len(context.events),
               context.events[0].time_left.seconds))
    else:
        print("No events registered")

    for th in context.cnsr_thrd:
        if th.is_alive():
            print(("#" * 15 + " Stack trace for thread %u " + "#" * 15) %
                  th.ident)
            traceback.print_stack(sys._current_frames()[th.ident])


@hook("prompt_cmd", "netstat")
def netstat(toks, context, **kwargs):
    """Display sockets in use and many other things"""
    if len(context.network) > 0:
        print("Distant bots connected: %d:" % len(context.network))
        for name, bot in context.network.items():
            print("# %s:" % name)
            print("  * Declared hooks:")
            lvl = 0
            for hlvl in bot.hooks:
                lvl += 1
                for hook in (hlvl.all_pre + hlvl.all_post + hlvl.cmd_rgxp +
                             hlvl.cmd_default + hlvl.ask_rgxp +
                             hlvl.ask_default + hlvl.msg_rgxp +
                             hlvl.msg_default):
                    print("  %s- %s" % (' ' * lvl * 2, hook))
                for kind in ["irc_hook", "cmd_hook", "ask_hook", "msg_hook"]:
                    print("  %s- <%s> %s" % (' ' * lvl * 2, kind,
                                             ", ".join(hlvl.__dict__[kind].keys())))
            print("  * My tag: %d" % bot.my_tag)
            print("  * Tags in use (%d):" % bot.inc_tag)
            for tag, (cmd, data) in bot.tags.items():
                print("    - %11s: %s « %s »" % (tag, cmd, data))
    else:
        print("No distant bot connected")
