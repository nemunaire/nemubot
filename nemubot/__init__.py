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

from datetime import datetime, timedelta, timezone
import imp
import ipaddress
import logging
import os
from queue import Queue
import re
from select import select
import threading
import time
import uuid

__version__ = '4.0.dev0'
__author__  = 'nemunaire'

from nemubot.consumer import Consumer, EventConsumer, MessageConsumer
from nemubot import datastore
from nemubot.event import ModuleEvent
from nemubot.hooks.messagehook import MessageHook
from nemubot.hooks.manager import HooksManager
from nemubot.networkbot import NetworkBot

logger = logging.getLogger("nemubot")


class Bot(threading.Thread):

    """Class containing the bot context and ensuring key goals"""

    def __init__(self, ip="127.0.0.1", modules_paths=list(),
                 data_store=datastore.Abstract(), verbosity=0):
        """Initialize the bot context

        Keyword arguments:
        ip -- The external IP of the bot (default: 127.0.0.1)
        modules_paths -- Paths to all directories where looking for module
        data_store -- An instance of the nemubot datastore for bot's modules
        """

        threading.Thread.__init__(self)

        logger.info("Initiate nemubot v%s", __version__)

        self.verbosity = verbosity

        # External IP for accessing this bot
        self.ip = ipaddress.ip_address(ip)

        # Context paths
        self.modules_paths = modules_paths
        self.datastore = data_store
        self.datastore.open()

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
            if re.match("^ *(m[' ]?entends?[ -]+tu|h?ear me|do you copy|ping)", msg.message, re.I) is not None:
                return msg.respond("pong")
        self.hooks.add_hook(MessageHook(in_ping), "in", "DirectAsk")

        def _help_msg(msg):
            """Parse and response to help messages"""
            from more import Response
            res = Response(channel=msg.frm)
            if len(msg.args) > 1:
                if msg.args[0] in self.modules:
                    if len(msg.args) > 2:
                        if hasattr(self.modules[msg.args[0]], "HELP_cmd"):
                            res.append_message(self.modules[msg.args[0]].HELP_cmd(msg.args[1]))
                        else:
                            res.append_message("No help for command %s in module %s" % (msg.args[1], msg.args[0]))
                    elif hasattr(self.modules[msg.args[0]], "help_full"):
                        res.append_message(self.modules[msg.args[0]].help_full())
                    else:
                        res.append_message("No help for module %s" % msg.args[0])
                else:
                    res.append_message("No module named %s" % msg.args[0])
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
        self.hooks.add_hook(MessageHook(_help_msg, "help"), "in", "Command")

        # Other known bots, making a bots network
        self.network     = dict()

        # Messages to be treated
        self.cnsr_queue     = Queue()
        self.cnsr_thrd      = list()
        self.cnsr_thrd_size = -1


    def run(self):
        from nemubot.server import _rlist, _wlist, _xlist

        self.stop = False
        while not self.stop:
            try:
                rl, wl, xl = select(_rlist, _wlist, _xlist, 0.1)
            except:
                logger.error("Something went wrong in select")
                fnd_smth = False
                # Looking for invalid server
                for r in _rlist:
                    if not hasattr(r, "fileno") or not isinstance(r.fileno(), int):
                        _rlist.remove(r)
                        logger.error("Found invalid object in _rlist: " + r)
                        fnd_smth = True
                for w in _wlist:
                    if not hasattr(r, "fileno") or not isinstance(w.fileno(), int):
                        _wlist.remove(w)
                        logger.error("Found invalid object in _wlist: " + w)
                        fnd_smth = True
                for x in _xlist:
                    if not hasattr(r, "fileno") or not isinstance(x.fileno(), int):
                        _xlist.remove(x)
                        logger.error("Found invalid object in _xlist: " + x)
                        fnd_smth = True
                if not fnd_smth:
                    logger.exception("Can't continue, sorry")
                    self.stop = True
                continue

            for x in xl:
                try:
                    x.exception()
                except:
                    logger.exception("Uncatched exception on server exception")
            for w in wl:
                try:
                    w.write_select()
                except:
                    logger.exception("Uncatched exception on server write")
            for r in rl:
                for i in r.read():
                    try:
                        self.receive_message(r, i)
                    except:
                        logger.exception("Uncatched exception on server read")


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
                module_src.REGISTERED_EVENTS.remove(id)
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
            if datetime.now(timezone.utc) + timedelta(seconds=5) >= self.events[0].current:
                while datetime.now(timezone.utc) < self.events[0].current:
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

        while len(self.events) > 0 and datetime.now(timezone.utc) >= self.events[0].current:
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


    def add_server(self, srv, autoconnect=True):
        """Add a new server to the context

        Arguments:
        srv -- a concrete AbstractServer instance
        autoconnect -- connect after add?
        """

        if srv.id not in self.servers:
            self.servers[srv.id] = srv
            if (autoconnect and not hasattr(self, "noautoconnect") and
                hasattr(self, "stop") and not self.stop):
                srv.open()
            return True

        else:
            return False


    # Modules methods

    def import_module(self, name):
        """Load a module

        Argument:
        name -- name of the module to load
        """

        if name in self.modules:
            self.unload_module(name)
            tt = __import__(name)
            imp.reload(tt)
        else:
            __import__(name)


    def add_module(self, module):
        """Add a module to the context, if already exists, unload the
        old one before"""
        # Check if the module already exists
        if module.__name__ in self.modules:
            self.unload_module(module.__name__)

        # Overwrite print built-in
        def prnt(*args):
            print("[%s]" % module.__name__, *args)
            if hasattr(module, "logger"):
                module.logger.info(" ".join(args))
        module.print = prnt

        self.modules[module.__name__] = module
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

        self.datastore.close()

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


def hotswap(bak):
    bak.stop = True
    if bak.event_timer is not None:
        bak.event_timer.cancel()
    bak.datastore.close()

    new = Bot(str(bak.ip), bak.modules_paths, bak.datastore)
    new.servers = bak.servers
    new.modules = bak.modules
    new.modules_configuration = bak.modules_configuration
    new.events = bak.events
    new.hooks = bak.hooks
    new.network = bak.network

    new._update_event_timer()
    return new

def reload():
    import nemubot.channel
    imp.reload(nemubot.channel)

    import nemubot.consumer
    imp.reload(nemubot.consumer)

    import nemubot.event
    imp.reload(nemubot.event)

    import nemubot.exception
    imp.reload(nemubot.exception)

    import nemubot.hooks
    imp.reload(nemubot.hooks)

    nemubot.hooks.reload()

    import nemubot.importer
    imp.reload(nemubot.importer)

    import nemubot.message
    imp.reload(nemubot.message)

    nemubot.message.reload()

    import nemubot.prompt
    imp.reload(nemubot.prompt)

    nemubot.prompt.reload()

    import nemubot.server
    rl, wl, xl = nemubot.server._rlist, nemubot.server._wlist, nemubot.server._xlist
    imp.reload(nemubot.server)
    nemubot.server._rlist, nemubot.server._wlist, nemubot.server._xlist = rl, wl, xl

    nemubot.server.reload()

    import nemubot.tools
    imp.reload(nemubot.tools)

    nemubot.tools.reload()
