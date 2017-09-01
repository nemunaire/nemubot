# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2016  Mercier Pierre-Olivier
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

import asyncio
from datetime import datetime, timezone
import logging
from multiprocessing import JoinableQueue
import threading
import traceback
import select
import sys
import weakref

from nemubot import __version__
from nemubot.consumer import Consumer, EventConsumer, MessageConsumer
from nemubot import datastore
import nemubot.hooks

logger = logging.getLogger("nemubot")

sync_queue = JoinableQueue()

def sync_act(*args):
    sync_queue.put(list(args))


class Bot(threading.Thread):

    """Class containing the bot context and ensuring key goals"""

    def __init__(self, ip="127.0.0.1", modules_paths=list(),
                 data_store=datastore.Abstract(), debug=False, loop=None):
        """Initialize the bot context

        Keyword arguments:
        ip -- The external IP of the bot (default: 127.0.0.1)
        modules_paths -- Paths to all directories where looking for modules
        data_store -- An instance of the nemubot datastore for bot's modules
        debug -- enable debug
        """

        super().__init__(name="Nemubot main")

        logger.info("Initiate nemubot v%s (running on Python %s.%s.%s)",
                    __version__,
                    sys.version_info.major, sys.version_info.minor, sys.version_info.micro)

        self.debug = debug
        self.stop = None

        #
        self.loop = loop if loop is not None else asyncio.get_event_loop()

        # Those events are used to ensure there is always one event in the next 24h, else overflow can occurs on loop timeout
        def event_sentinel(offset=43210):
            logger.debug("Defining new event sentinelle in %ss", 43210 + offset)
            self.loop.call_later(43210 + offset, event_sentinel)
        event_sentinel(0)
        event_sentinel(43210)

        # External IP for accessing this bot
        import ipaddress
        self.ip = ipaddress.ip_address(ip)

        # Context paths
        self.modules_paths = modules_paths
        self.datastore = data_store
        self.datastore.open()

        # Keep global context: servers and modules
        self._poll = select.poll()
        self.servers = dict()
        self.modules = dict()
        self.modules_configuration = dict()

        # Own hooks
        from nemubot.treatment import MessageTreater
        self.treater     = MessageTreater()

        import re
        def in_ping(msg):
            return msg.respond("pong")
        self.treater.hm.add_hook(nemubot.hooks.Message(in_ping,
                                                       match=lambda msg: re.match("^ *(m[' ]?entends?[ -]+tu|h?ear me|do you copy|ping)",
                                                                                  msg.message, re.I)),
                                 "in", "DirectAsk")

        def in_echo(msg):
            from nemubot.message import Text
            return Text(msg.frm + ": " + " ".join(msg.args), to=msg.to_response)
        self.treater.hm.add_hook(nemubot.hooks.Command(in_echo, "echo"), "in", "Command")

        def _help_msg(msg):
            """Parse and response to help messages"""
            from nemubot.module.more import Response
            res = Response(channel=msg.to_response)
            if len(msg.args) >= 1:
                if "nemubot.module." + msg.args[0] in self.modules and self.modules["nemubot.module." + msg.args[0]]() is not None:
                    mname = "nemubot.module." + msg.args[0]
                    if hasattr(self.modules[mname](), "help_full"):
                        hlp = self.modules[mname]().help_full()
                        if isinstance(hlp, Response):
                            return hlp
                        else:
                            res.append_message(hlp)
                    else:
                        res.append_message([str(h) for s,h in self.modules[mname]().__nemubot_context__.hooks], title="Available commands for module " + msg.args[0])
                elif msg.args[0][0] == "!":
                    from nemubot.message.command import Command
                    for h in self.treater._in_hooks(Command(msg.args[0][1:])):
                        if h.help_usage:
                            lp = ["\x03\x02%s%s\x03\x02: %s" % (msg.args[0], (" " + k if k is not None else ""), h.help_usage[k]) for k in h.help_usage]
                            jp = h.keywords.help()
                            return res.append_message(lp + ([". Moreover, you can provides some optional parameters: "] + jp if len(jp) else []), title="Usage for command %s" % msg.args[0])
                        elif h.help:
                            return res.append_message("Command %s: %s" % (msg.args[0], h.help))
                        else:
                            return res.append_message("Sorry, there is currently no help for the command %s. Feel free to make a pull request at https://github.com/nemunaire/nemubot/compare" % msg.args[0])
                    res.append_message("Sorry, there is no command %s" % msg.args[0])
                else:
                    res.append_message("Sorry, there is no module named %s" % msg.args[0])
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
                                   message=["\x03\x02%s\x03\x02 (%s)" % (im, self.modules[im]().__doc__) for im in self.modules if self.modules[im]() is not None and self.modules[im]().__doc__])
            return res
        self.treater.hm.add_hook(nemubot.hooks.Command(_help_msg, "help"), "in", "Command")

        from queue import Queue
        # Messages to be treated
        self.cnsr_queue     = Queue()
        self.cnsr_thrd      = list()
        self.cnsr_thrd_size = -1


    def __del__(self):
        self.datastore.close()


    def run(self):
        global sync_queue

        # Rewrite the sync_queue, as the daemonization process tend to disturb it
        old_sync_queue, sync_queue = sync_queue, JoinableQueue()
        while not old_sync_queue.empty():
            sync_queue.put_nowait(old_sync_queue.get())

        self._poll.register(sync_queue._reader, select.POLLIN | select.POLLPRI)

        logger.info("Starting main loop")
        self.stop = False
        while not self.stop:
            for fd, flag in self._poll.poll():
                # Handle internal socket passing orders
                if fd != sync_queue._reader.fileno() and fd in self.servers:
                    srv = self.servers[fd]

                    if flag & (select.POLLERR | select.POLLHUP | select.POLLNVAL):
                        try:
                            srv.exception(flag)
                        except:
                            logger.exception("Uncatched exception on server exception")

                    if srv.fileno() > 0:
                        if flag & (select.POLLOUT):
                            try:
                                srv.async_write()
                            except:
                                logger.exception("Uncatched exception on server write")

                        if flag & (select.POLLIN | select.POLLPRI):
                            try:
                                for i in srv.async_read():
                                    self.receive_message(srv, i)
                            except:
                                logger.exception("Uncatched exception on server read")

                    else:
                        del self.servers[fd]


                # Always check the sync queue
                while not sync_queue.empty():
                    args = sync_queue.get()
                    action = args.pop(0)

                    logger.debug("Executing sync_queue action %s%s", action, args)

                    if action == "sckt" and len(args) >= 2:
                        try:
                            if args[0] == "write":
                                self._poll.modify(int(args[1]), select.POLLOUT | select.POLLIN | select.POLLPRI)
                            elif args[0] == "unwrite":
                                self._poll.modify(int(args[1]), select.POLLIN | select.POLLPRI)

                            elif args[0] == "register":
                                self._poll.register(int(args[1]), select.POLLIN | select.POLLPRI)
                            elif args[0] == "unregister":
                                self._poll.unregister(int(args[1]))
                        except:
                            logger.exception("Unhandled excpetion during action:")

                    elif action == "exit":
                        self.quit()

                    elif action == "launch_consumer":
                        pass  # This is treated after the loop

                    sync_queue.task_done()


            # Launch new consumer threads if necessary
            while self.cnsr_queue.qsize() > self.cnsr_thrd_size:
                # Next launch if two more items in queue
                self.cnsr_thrd_size += 2

                c = Consumer(self)
                self.cnsr_thrd.append(c)
                c.start()
        sync_queue = None
        logger.info("Ending main loop")



    # Events methods

    @asyncio.coroutine
    def _call_at(self, when, *args, **kwargs):
        @asyncio.coroutine
        def _add_event():
            return self.loop.call_at(when, *args, **kwargs)
        future = yield from asyncio.run_coroutine_threadsafe(_add_event(), loop=self.loop)
        logger.debug("New event registered, scheduled in %ss", when - self.loop.time())
        return future.result()


    def call_at(self, when, *args, **kwargs):
        delay = (when - datetime.now(timezone.utc)).total_seconds()
        return self._call_at(self.loop.time() + delay, *args, **kwargs)


    def call_delay(self, delay, *args, **kwargs):
        return self._call_at(self.loop.time() + delay, *args, **kwargs)


    def add_event(self, evt):
        """Register an event and return its identifiant for futur update

        Return:
        None if the event is not in the queue (eg. if it has been executed during the call) or
        returns the event ID.

        Argument:
        evt -- The event object to add
        """

        if hasattr(evt, "handle") and evt.handle is not None:
            raise Exception("Try to launch an already launched event.")

        def _end_event_timer(event):
            """Function called at the end of the event timer"""

            logger.debug("Trigering event")
            event.handle = None
            self.cnsr_queue.put_nowait(EventConsumer(event))
            sync_act("launch_consumer")

        evt.start(self.loop)
        evt.handle = call_at(evt._next, _end_event_timer, evt)

        logger.debug("New event registered in %ss", evt._next - self.loop.time())

        return evt.handle



    # Consumers methods

    def add_server(self, srv, autoconnect=True):
        """Add a new server to the context

        Arguments:
        srv -- a concrete AbstractServer instance
        autoconnect -- connect after add?
        """

        fileno = srv.fileno()
        if fileno not in self.servers:
            self.servers[fileno] = srv
            self.servers[srv.name] = srv
            if autoconnect and not hasattr(self, "noautoconnect"):
                srv.connect()
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

        __import__(name)


    def add_module(self, module):
        """Add a module to the context, if already exists, unload the
        old one before"""

        import nemubot.hooks

        self.loop.call_soon_threadsafe(self._add_module,
                                       module,
                                       nemubot.hooks.hook.last_registered)

        nemubot.hooks.hook.last_registered = []


    def _add_module(self, module, registered_functions):
        module_name = module.__spec__.name if hasattr(module, "__spec__") else module.__name__

        if hasattr(self, "stop") and self.stop:
            logger.warn("The bot is stopped, can't register new modules")
            return

        # Check if the module already exists
        if module_name in self.modules:
            self.unload_module(module_name)

        # Overwrite print built-in
        def prnt(*args):
            if hasattr(module, "logger"):
                module.logger.info(" ".join([str(s) for s in args]))
            else:
                logger.info("[%s] %s", module_name, " ".join([str(s) for s in args]))
        module.print = prnt

        # Create module context
        from nemubot.modulecontext import _ModuleContext, ModuleContext
        module.__nemubot_context__ = ModuleContext(self, module)

        if not hasattr(module, "logger"):
            module.logger = logging.getLogger("nemubot.module." + module_name)

        # Replace imported context by real one
        for attr in module.__dict__:
            if attr != "__nemubot_context__" and type(module.__dict__[attr]) == _ModuleContext:
                module.__dict__[attr] = module.__nemubot_context__

        # Register decorated functions
        for s, h in registered_functions:
            module.__nemubot_context__.add_hook(h, *s if isinstance(s, list) else s)

        # Launch the module
        if hasattr(module, "load"):
            try:
                module.load(module.__nemubot_context__)
            except:
                module.__nemubot_context__.unload()
                raise

        # Save a reference to the module
        self.modules[module_name] = weakref.ref(module)
        logger.info("Module '%s' successfully loaded.", module_name)


    def unload_module(self, name):
        """Unload a module"""
        if name in self.modules and self.modules[name]() is not None:
            module = self.modules[name]()
            module.print("Unloading module %s" % name)

            # Call the user defined unload method
            if hasattr(module, "unload"):
                module.unload(self)
            module.__nemubot_context__.unload()

            # Remove from the nemubot dict
            del self.modules[name]

            # Remove from the Python dict
            del sys.modules[name]
            for mod in [i for i in sys.modules]:
                if mod[:len(name) + 1] == name + ".":
                    logger.debug("Module '%s' also removed from system modules list.", mod)
                    del sys.modules[mod]

            logger.info("Module `%s' successfully unloaded.", name)

            return True
        return False


    def receive_message(self, srv, msg):
        """Queued the message for treatment

        Arguments:
        srv -- The server where the message comes from
        msg -- The message not parsed, as simple as possible
        """

        self.cnsr_queue.put_nowait(MessageConsumer(srv, msg))


    def quit(self):
        """Save and unload modules and disconnect servers"""

        logger.info("Save and unload all modules...")
        for mod in [m for m in self.modules.keys()]:
            self.unload_module(mod)

        logger.info("Close all servers connection...")
        for srv in [self.servers[k] for k in self.servers]:
            srv.close()

        logger.info("Stop consumers")
        k = self.cnsr_thrd
        for cnsr in k:
            cnsr.stop = True

        logger.info("Closing event loop")
        self.loop.stop()

        if self.stop is False or sync_queue is not None:
            self.stop = True
            sync_act("end")
            sync_queue.join()


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
