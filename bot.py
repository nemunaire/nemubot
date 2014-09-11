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
from datetime import timedelta
import logging
from queue import Queue
import re
from select import select
import threading
import time
import uuid

__version__ = '3.4.dev0'
__author__  = 'nemunaire'

from consumer import Consumer, EventConsumer, MessageConsumer
from event import ModuleEvent
from hooks.messagehook import MessageHook
from hooks.manager import HooksManager
from networkbot import NetworkBot
from server.IRC import IRCServer
from server.DCC import DCC
import response

logger = logging.getLogger("nemubot.bot")

class Bot(threading.Thread):

    """Class containing the bot context and ensuring key goals"""

    def __init__(self, ip="127.0.0.1", modules_paths=list(), data_path="./datas/"):
        """Initialize the bot context

        Keyword arguments:
        ip -- The external IP of the bot (default: 127.0.0.1)
        modules_paths -- Paths to all directories where looking for module
        data_path -- Path to directory where store bot context data
        """

        threading.Thread.__init__(self)

        logger.info("Initiate nemubot v%s", __version__)

        # External IP for accessing this bot
        self.ip = ip

        # Context paths
        self.modules_paths = modules_paths
        self.data_path = data_path

        # Save various informations
        self.ctcp_capabilities = dict()
        self.init_ctcp_capabilities()

        # Keep global context: servers and modules
        self.servers = dict()
        self.modules = dict()
        self.modules_configuration = dict()

        # Events
        self.events      = list()
        self.event_timer = None

        # Own hooks
        self.hooks       = HooksManager()
        def in_ping(msg):
            if re.match("^ *(m[' ]?entends?[ -]+tu|h?ear me|do you copy|ping)", msg.text, re.I) is not None:
                return response.Response(msg.sender, message="pong", channel=msg.receivers, nick=msg.nick)
        self.hooks.add_hook(MessageHook(in_ping), "in", "PRIVMSG")

        def _help_msg(msg):
            """Parse and response to help messages"""
            cmd = msg.cmds
            sndr = msg.sender
            res = response.Response(sndr)
            if len(cmd) > 1:
                if cmd[1] in self.modules:
                    if len(cmd) > 2:
                        if hasattr(self.modules[cmd[1]], "HELP_cmd"):
                            res.append_message(self.modules[cmd[1]].HELP_cmd(cmd[2]))
                        else:
                            res.append_message("No help for command %s in module %s" % (cmd[2], cmd[1]))
                    elif hasattr(self.modules[cmd[1]], "help_full"):
                        res.append_message(self.modules[cmd[1]].help_full())
                    else:
                        res.append_message("No help for module %s" % cmd[1])
                else:
                    res.append_message("No module named %s" % cmd[1])
            else:
                res.append_message("Pour me demander quelque chose, commencez "
                                   "votre message par mon nom ; je réagis "
                                   "également à certaine commandes commençant par"
                                   " !.  Pour plus d'informations, envoyez le "
                                   "message \"!more\".")
                res.append_message("Mon code source est libre, publié sous "
                                   "licence AGPL (http://www.gnu.org/licenses/). "
                                   "Vous pouvez le consulter, le dupliquer, "
                                   "envoyer des rapports de bogues ou bien "
                                   "contribuer au projet sur GitHub : "
                                   "http://github.com/nemunaire/nemubot/")
                res.append_message(title="Pour plus de détails sur un module, "
                                   "envoyez \"!help nomdumodule\". Voici la liste"
                                   " de tous les modules disponibles localement",
                                   message=["\x03\x02%s\x03\x02 (%s)" % (im, self.modules[im].__doc__) for im in self.modules if self.modules[im].__doc__])
            return res
        self.hooks.add_hook(MessageHook(_help_msg, "help"), "in", "PRIVMSG", "cmd")

        # Other known bots, making a bots network
        self.network     = dict()
        self.hooks_cache = dict()

        # Messages to be treated
        self.cnsr_queue     = Queue()
        self.cnsr_thrd      = list()
        self.cnsr_thrd_size = -1


    def run(self):
        from server import _rlist, _wlist, _xlist

        self.stop = False
        while not self.stop:
            rl, wl, xl = select(_rlist, _wlist, _xlist, 0.1)

            for x in xl:
                x.exception()
            for w in wl:
                w.write_select()
            for r in rl:
                for i in r.read():
                    self.receive_message(r, i)


    def init_ctcp_capabilities(self):
        """Reset existing CTCP capabilities to default one"""

        def _ctcp_clientinfo(srv, msg):
            """Response to CLIENTINFO CTCP message"""
            return _ctcp_response(msg.sender,
                                  " ".join(self.ctcp_capabilities.keys()))

        def _ctcp_dcc(srv, msg):
            """Response to DCC CTCP message"""
            try:
                ip = srv.toIP(int(msg.cmds[3]))
                port = int(msg.cmds[4])
                conn = DCC(srv, msg.sender)
            except:
                return _ctcp_response(msg.sender, "ERRMSG invalid parameters provided as DCC CTCP request")

            logger.info("Receive DCC connection request from %s to %s:%d", conn.sender, ip, port)

            if conn.accept_user(ip, port):
                srv.dcc_clients[conn.sender] = conn
                conn.send_dcc("Hello %s!" % conn.nick)
            else:
                logger.error("DCC: unable to connect to %s:%d", ip, port)
                return _ctcp_response(msg.sender, "ERRMSG unable to connect to %s:%d" % (ip, port))

        self.ctcp_capabilities["ACTION"] = lambda srv, msg: print ("ACTION receive: %s" % msg.text)
        self.ctcp_capabilities["CLIENTINFO"] = _ctcp_clientinfo
        self.ctcp_capabilities["DCC"] = _ctcp_dcc
        self.ctcp_capabilities["FINGER"] = lambda srv, msg: _ctcp_response(
            msg.sender, "VERSION nemubot v%s" % __version__)
        self.ctcp_capabilities["NEMUBOT"] = lambda srv, msg: _ctcp_response(
            msg.sender, "NEMUBOT %s" % __version__)
        self.ctcp_capabilities["PING"] = lambda srv, msg: _ctcp_response(
            msg.sender, "PING %s" % " ".join(msg.cmds[1:]))
        self.ctcp_capabilities["SOURCE"] = lambda srv, msg: _ctcp_response(
            msg.sender, "SOURCE https://github.com/nemunaire/nemubot")
        self.ctcp_capabilities["TIME"] = lambda srv, msg: _ctcp_response(
            msg.sender, "TIME %s" % (datetime.now()))
        self.ctcp_capabilities["USERINFO"] = lambda srv, msg: _ctcp_response(
            msg.sender, "USERINFO %s" % srv.realname)
        self.ctcp_capabilities["VERSION"] = lambda srv, msg: _ctcp_response(
            msg.sender, "VERSION nemubot v%s" % __version__)

        logger.debug("CTCP capabilities setup: %s", ", ".join(self.ctcp_capabilities))


    # Events methods

    def add_event(self, evt, eid=None, module_src=None):
        """Register an event and return its identifiant for futur update

        Return:
        None if the event is not in the queue (eg. if it has been executed during the call) or
        returns the event ID.

        Argument:
        evt -- The event object to add

        Keyword arguments:
        eid -- The desired event ID (object or string UUID)
        module_src -- The module to which the event is attached to
        """

        # Generate the event id if no given
        if eid is None:
            eid = uuid.uuid1()

        # Fill the id field of the event
        if type(eid) is uuid.UUID:
            evt.id = str(eid)
        else:
            # Ok, this is quite useless...
            try:
                evt.id = str(uuid.UUID(eid))
            except ValueError:
                evt.id = eid

        # Add the event in its place
        t = evt.current
        i = 0 # sentinel
        for i in range(0, len(self.events)):
            if self.events[i].current > t:
                break
        self.events.insert(i, evt)

        if i == 0:
            # First event changed, reset timer
            self._update_event_timer()
            if len(self.events) <= 0 or self.events[i] != evt:
                # Our event has been executed and removed from queue
                return None

        # Register the event in the source module
        if module_src is not None:
            module_src.REGISTERED_EVENTS.append(evt.id)
        evt.module_src = module_src

        logger.info("New event registered: %s -> %s", evt.id, evt)
        return evt.id


    def del_event(self, evt, module_src=None):
        """Find and remove an event from list

        Return:
        True if the event has been found and removed, False else

        Argument:
        evt -- The ModuleEvent object to remove or just the event identifier

        Keyword arguments:
        module_src -- The module to which the event is attached to (ignored if evt is a ModuleEvent)
        """

        logger.info("Removing event: %s from %s", evt, module_src)

        if type(evt) is ModuleEvent:
            id = evt.id
            module_src = evt.module_src
        else:
            id = evt

        if len(self.events) > 0 and id == self.events[0].id:
            self.events.remove(self.events[0])
            self._update_event_timer()
            if module_src is not None:
                module_src.REGISTERED_EVENTS.remove(evt.id)
            return True

        for evt in self.events:
            if evt.id == id:
                self.events.remove(evt)

                if module_src is not None:
                    module_src.REGISTERED_EVENTS.remove(evt.id)
                return True
        return False


    def _update_event_timer(self):
        """(Re)launch the timer to end with the closest event"""

        # Reset the timer if this is the first item
        if self.event_timer is not None:
            self.event_timer.cancel()

        if len(self.events) > 0:
            logger.debug("Update timer: next event in %d seconds",
                         self.events[0].time_left.seconds)
            if datetime.now() + timedelta(seconds=5) >= self.events[0].current:
                while datetime.now() < self.events[0].current:
                    time.sleep(0.6)
                self._end_event_timer()
            else:
                self.event_timer = threading.Timer(
                    self.events[0].time_left.seconds + 1, self._end_event_timer)
                self.event_timer.start()
        else:
            logger.debug("Update timer: no timer left")


    def _end_event_timer(self):
        """Function called at the end of the event timer"""

        while len(self.events) > 0 and datetime.now() >= self.events[0].current:
            evt = self.events.pop(0)
            self.cnsr_queue.put_nowait(EventConsumer(evt))
            self._launch_consumers()

        self._update_event_timer()


    # Consumers methods

    def _launch_consumers(self):
        """Launch new consumer threads if necessary"""

        while self.cnsr_queue.qsize() > self.cnsr_thrd_size:
            # Next launch if two more items in queue
            self.cnsr_thrd_size += 2

            c = Consumer(self)
            self.cnsr_thrd.append(c)
            c.start()


    def add_server(self, node, nick, owner, realname):
        """Add a new server to the context"""
        srv = IRCServer(node, nick, owner, realname)
        #srv.register_hooks()
        if srv.id not in self.servers:
            self.servers[srv.id] = srv
            srv.open()
            return True
        else:
            return False


    # Modules methods

    def add_modules_path(self, path):
        """Add a path to the modules_path array, used by module loader"""
        # The path must end by / char
        if path[-1] != "/":
            path += "/"

        if path not in self.modules_paths:
            self.modules_paths.append(path)
            return True

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


    def unload_module(self, name):
        """Unload a module"""
        if name in self.modules:
            self.modules[name].print_debug("Unloading module %s" % name)
            self.modules[name].save()
            if hasattr(self.modules[name], "unload"):
                self.modules[name].unload(self)
            # Remove registered hooks
            for (s, h) in self.modules[name].REGISTERED_HOOKS:
                self.hooks.del_hook(h, s)
            # Remove registered events
            for e in self.modules[name].REGISTERED_EVENTS:
                self.del_event(e)
            # Remove from the dict
            del self.modules[name]
            logger.info("Module `%s' successfully unloaded.", name)
            return True
        return False


    def receive_message(self, srv, msg, private=False, data=None):
        """Queued the message for treatment"""
        #print("READ", raw_msg)
        self.cnsr_queue.put_nowait(MessageConsumer(srv, msg))

        # Launch a new thread if necessary
        self._launch_consumers()


    def add_networkbot(self, srv, dest, dcc=None):
        """Append a new bot into the network"""
        id = srv.id + "/" + dest
        if id not in self.network:
            self.network[id] = NetworkBot(self, srv, dest, dcc)
        return self.network[id]

    def send_networkbot(self, srv, cmd, data=None):
        for bot in self.network:
            if self.network[bot].srv == srv:
                self.network[bot].send_cmd(cmd, data)

    def quit(self):
        """Save and unload modules and disconnect servers"""
        if self.event_timer is not None:
            logger.info("Stop the event timer...")
            self.event_timer.cancel()

        logger.info("Save and unload all modules...")
        k = list(self.modules.keys())
        for mod in k:
            self.unload_module(mod)

        logger.info("Close all servers connection...")
        k = list(self.servers.keys())
        for srv in k:
            self.servers[srv].close()

        self.stop = True


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


def _ctcp_response(sndr, msg):
    return response.Response(sndr, msg, ctcp=True)

def hotswap(bak):
    bak.stop = True
    new = Bot(str(bak.ip), bak.modules_paths, bak.data_path)
    new.ctcp_capabilities = bak.ctcp_capabilities
    new.servers = bak.servers
    new.modules = bak.modules
    new.modules_configuration = bak.modules_configuration
    new.events = bak.events
    new.hooks = bak.hooks
    new.network = bak.network
    return new

def reload():
    import imp

    import channel
    imp.reload(channel)

    import consumer
    imp.reload(consumer)

    import event
    imp.reload(event)

    import exception
    imp.reload(exception)

    import hooks
    imp.reload(hooks)
    import hooks.manager
    imp.reload(hooks.manager)
    import hooks.messagehook
    imp.reload(hooks.messagehook)

    import importer
    imp.reload(importer)

    import message
    imp.reload(message)

    import prompt
    imp.reload(prompt)
    import prompt.builtins
    imp.reload(prompt.builtins)

    import response
    imp.reload(response)

    import server
    rl,wl,xl = server._rlist,server._wlist,server._xlist
    imp.reload(server)
    server._rlist,server._wlist,server._xlist = rl,wl,xl
    import server.socket
    imp.reload(server.socket)
    import server.IRC
    imp.reload(server.IRC)

    import tools
    imp.reload(tools)
    import tools.countdown
    imp.reload(tools.countdown)
    import tools.date
    imp.reload(tools.date)
    import tools.web
    imp.reload(tools.web)
    import tools.wrapper
    imp.reload(tools.wrapper)

    import xmlparser
    imp.reload(xmlparser)
    import xmlparser.node
    imp.reload(xmlparser.node)
