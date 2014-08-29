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
import threading
import time
import uuid

__version__ = '3.4.dev0'
__author__  = 'nemunaire'

from consumer import Consumer, EventConsumer, MessageConsumer
from event import ModuleEvent
import hooks
from networkbot import NetworkBot
from server.IRC import IRCServer
from server.DCC import DCC
import response

logger = logging.getLogger("nemubot.bot")

class Bot:

    """Class containing the bot context and ensuring key goals"""

    def __init__(self, ip="127.0.0.1", modules_paths=list(), data_path="./datas/"):
        """Initialize the bot context

        Keyword arguments:
        ip -- The external IP of the bot (default: 127.0.0.1)
        modules_paths -- Paths to all directories where looking for module
        data_path -- Path to directory where store bot context data
        """

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
        self.hooks       = hooks.MessagesHook(self, self)

        # Other known bots, making a bots network
        self.network     = dict()
        self.hooks_cache = dict()

        # Messages to be treated
        self.cnsr_queue     = Queue()
        self.cnsr_thrd      = list()
        self.cnsr_thrd_size = -1

        self.hooks.add_hook("irc_hook",
                            hooks.Hook(self.treat_prvmsg, "PRIVMSG"),
                            self)


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


    def add_server(self, node, nick, owner, realname, ssl=False):
        """Add a new server to the context"""
        srv = IRCServer(node, nick, owner, realname, ssl)
        srv.add_hook = lambda h: self.hooks.add_hook("irc_hook", h, self)
        srv.add_networkbot = self.add_networkbot
        srv.send_bot = lambda d: self.send_networkbot(srv, d)
        srv.register_hooks()
        if srv.id not in self.servers:
            self.servers[srv.id] = srv
            if srv.autoconnect:
                srv.launch(self.receive_message)
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
                self.hooks.del_hook(s, h)
            # Remove registered events
            for e in self.modules[name].REGISTERED_EVENTS:
                self.del_event(e)
            # Remove from the dict
            del self.modules[name]
            logger.info("Module `%s' successfully unloaded.", name)
            return True
        return False


    def receive_message(self, srv, raw_msg, private=False, data=None):
        """Queued the message for treatment"""
        #print (raw_msg)
        self.cnsr_queue.put_nowait(MessageConsumer(srv, raw_msg, datetime.now(), private, data))

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
            self.servers[srv].disconnect()

    # Hooks cache

    def create_cache(self, name):
        if name not in self.hooks_cache:
            if isinstance(self.hooks.__dict__[name], list):
                self.hooks_cache[name] = list()

                # Start by adding locals hooks
                for h in self.hooks.__dict__[name]:
                    tpl = (h, 0, self.hooks.__dict__[name], self.hooks.bot)
                    self.hooks_cache[name].append(tpl)

                # Now, add extermal hooks
                level = 0
                while level == 0 or lvl_exist:
                    lvl_exist = False
                    for ext in self.network:
                        if len(self.network[ext].hooks) > level:
                            lvl_exist = True
                            for h in self.network[ext].hooks[level].__dict__[name]:
                                if h not in self.hooks_cache[name]:
                                    self.hooks_cache[name].append((h, level + 1,
                                                                   self.network[ext].hooks[level].__dict__[name], self.network[ext].hooks[level].bot))
                    level += 1

            elif isinstance(self.hooks.__dict__[name], dict):
                self.hooks_cache[name] = dict()

                # Start by adding locals hooks
                for h in self.hooks.__dict__[name]:
                    self.hooks_cache[name][h] = (self.hooks.__dict__[name][h], 0,
                                                 self.hooks.__dict__[name],
                                                 self.hooks.bot)

                # Now, add extermal hooks
                level = 0
                while level == 0 or lvl_exist:
                    lvl_exist = False
                    for ext in self.network:
                        if len(self.network[ext].hooks) > level:
                            lvl_exist = True
                            for h in self.network[ext].hooks[level].__dict__[name]:
                                if h not in self.hooks_cache[name]:
                                    self.hooks_cache[name][h] = (self.network[ext].hooks[level].__dict__[name][h], level + 1, self.network[ext].hooks[level].__dict__[name], self.network[ext].hooks[level].bot)
                    level += 1

            else:
                raise Exception(name + " hook type unrecognized")

        return self.hooks_cache[name]

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

    def treat_pre(self, msg, srv):
        """Treat a message before all other treatment"""
        # Treat all messages starting with 'nemubot:' as distinct commands
        if msg.cmd == "PRIVMSG" and msg.text.find("%s:"%srv.nick) == 0:
            # Remove the bot name
            msg.text = msg.text[len(srv.nick)+1:].strip()
            msg.parse_content()
            msg.private = True

        for h, lvl, store, bot in self.create_cache("all_pre"):
            if h.is_matching(None, server=srv):
                h.run(msg, self.create_cache)
                self.check_rest_times(store, h)


    def treat_post(self, res):
        """Treat a message before send"""
        for h, lvl, store, bot in self.create_cache("all_post"):
            if h.is_matching(None, channel=res.channel, server=res.server):
                c = h.run(res)
                self.check_rest_times(store, h)
                if not c:
                    return False
        return True


    def treat_irc(self, msg, srv):
        """Treat all incoming IRC commands"""
        treated = list()

        irc_hooks = self.create_cache("irc_hook")
        if msg.cmd in irc_hooks:
            (hks, lvl, store, bot) = irc_hooks[msg.cmd]
            for h in hks:
                if h.is_matching(msg.cmd, server=srv):
                    res = h.run(msg, srv, msg.cmd)
                    if res is not None and res != False:
                        treated.append(res)
                    self.check_rest_times(store, h)

        return treated


    def treat_prvmsg_ask(self, msg, srv):
        # Treat ping
        if re.match("^ *(m[' ]?entends?[ -]+tu|h?ear me|do you copy|ping)",
                    msg.text, re.I) is not None:
            return response.Response(msg.sender, message="pong",
                                     channel=msg.receivers, nick=msg.nick)

        # Ask hooks
        else:
            return self.treat_ask(msg, srv)

    def treat_prvmsg(self, msg, srv):
        # First, treat CTCP
        if msg.is_ctcp:
            if msg.cmds[0] in self.ctcp_capabilities:
                return self.ctcp_capabilities[msg.cmds[0]](srv, msg)
            else:
                return _ctcp_response(msg.sender, "ERRMSG Unknown or unimplemented CTCP request")

        # Owner commands
        if len(msg.text) > 1 and msg.text[0] == '`' and msg.nick == srv.owner:
            #TODO: owner commands
            pass

        elif len(msg.text) > 1 and msg.text[0] == '!':
            # Remove the !
            msg.cmds[0] = msg.cmds[0][1:]

            if msg.cmds[0] == "help":
                return _help_msg(msg.sender, self.modules, msg.cmds)

            elif msg.cmds[0] == "more":
                if msg.receivers == srv.nick:
                    if msg.sender in srv.moremessages:
                        return srv.moremessages[msg.sender]
                else:
                    if msg.receivers in srv.moremessages:
                        return srv.moremessages[msg.receivers]

            elif msg.cmds[0] == "next":
                ret = None
                if msg.receivers == srv.nick:
                    if msg.sender in srv.moremessages:
                        ret = srv.moremessages[msg.sender]
                else:
                    if msg.receivers in srv.moremessages:
                        ret = srv.moremessages[msg.receivers]
                if ret is not None:
                    ret.pop()
                    return ret

            elif msg.cmds[0] == "dcc":
                logger.debug("dcctest for %s", msg.sender)
                srv.send_dcc("Hello %s!" % msg.nick, msg.sender)
            elif msg.cmds[0] == "pvdcctest":
                logger.debug("dcctest")
                return Response(msg.sender, message="Test DCC")
            elif msg.cmds[0] == "dccsendtest":
                logger.debug("dccsendtest")
                conn = DCC(srv, msg.sender)
                conn.send_file("bot_sample.xml")

            else:
                return self.treat_cmd(msg, srv)

        else:
            res = self.treat_answer(msg, srv)

            # Assume the message starts with nemubot:
            if not res and msg.private:
                return self.treat_prvmsg_ask(msg, srv)
            return res


    def treat_cmd(self, msg, srv):
        """Treat a command message"""
        treated = list()

        # First, treat simple hook
        cmd_hook = self.create_cache("cmd_hook")
        if msg.cmds[0] in cmd_hook:
            (hks, lvl, store, bot) = cmd_hook[msg.cmds[0]]
            for h in hks:
                if h.is_matching(msg.cmds[0], channel=msg.receivers, server=srv) and (msg.private or lvl == 0 or bot.nick not in srv.channels[msg.receivers].people):
                    res = h.run(msg, strcmp=msg.cmds[0])
                    if res is not None and res != False:
                        treated.append(res)
                    self.check_rest_times(store, h)

        # Then, treat regexp based hook
        cmd_rgxp = self.create_cache("cmd_rgxp")
        for hook, lvl, store, bot in cmd_rgxp:
            if hook.is_matching(msg.cmds[0], msg.receivers, server=srv) and (msg.private or lvl == 0 or bot.nick not in srv.channels[msg.receivers].people):
                res = hook.run(msg)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(store, hook)

        # Finally, treat default hooks if not catched before
        cmd_default = self.create_cache("cmd_default")
        for hook, lvl, store, bot in cmd_default:
            if treated:
                break
            res = hook.run(msg)
            if res is not None and res != False:
                treated.append(res)
            self.check_rest_times(store, hook)

        return treated

    def treat_ask(self, msg, srv):
        """Treat an ask message"""
        treated = list()

        # First, treat simple hook
        ask_hook = self.create_cache("ask_hook")
        if msg.text in ask_hook:
            hks, lvl, store, bot = ask_hook[msg.text]
            for h in hks:
                if h.is_matching(msg.text, channel=msg.receivers, server=srv) and (msg.private or lvl == 0 or bot.nick not in srv.channels[msg.receivers].people):
                    res = h.run(msg, strcmp=msg.text)
                    if res is not None and res != False:
                        treated.append(res)
                    self.check_rest_times(store, h)

        # Then, treat regexp based hook
        ask_rgxp = self.create_cache("ask_rgxp")
        for hook, lvl, store, bot in ask_rgxp:
            if hook.is_matching(msg.text, channel=msg.receivers, server=srv) and (msg.private or lvl == 0 or bot.nick not in srv.channels[msg.receivers].people):
                res = hook.run(msg, strcmp=msg.text)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(store, hook)

        # Finally, treat default hooks if not catched before
        ask_default = self.create_cache("ask_default")
        for hook, lvl, store, bot in ask_default:
            if treated:
                break
            res = hook.run(msg)
            if res is not None and res != False:
                treated.append(res)
            self.check_rest_times(store, hook)

        return treated

    def treat_answer(self, msg, srv):
        """Treat a normal message"""
        treated = list()

        # First, treat simple hook
        msg_hook = self.create_cache("msg_hook")
        if msg.text in msg_hook:
            hks, lvl, store, bot = msg_hook[msg.text]
            for h in hks:
                if h.is_matching(msg.text, channel=msg.receivers, server=srv) and (msg.private or lvl == 0 or bot.nick not in srv.channels[msg.receivers].people):
                    res = h.run(msg, strcmp=msg.text)
                    if res is not None and res != False:
                        treated.append(res)
                    self.check_rest_times(store, h)

        # Then, treat regexp based hook
        msg_rgxp = self.create_cache("msg_rgxp")
        for hook, lvl, store, bot in msg_rgxp:
            if hook.is_matching(msg.text, channel=msg.receivers, server=srv) and (msg.private or lvl == 0 or bot.nick not in srv.channels[msg.receivers].people):
                res = hook.run(msg, strcmp=msg.text)
                if res is not None and res != False:
                    treated.append(res)
                self.check_rest_times(store, hook)

        # Finally, treat default hooks if not catched before
        msg_default = self.create_cache("msg_default")
        for hook, lvl, store, bot in msg_default:
            if len(treated) > 0:
                break
            res = hook.run(msg)
            if res is not None and res != False:
                treated.append(res)
            self.check_rest_times(store, hook)

        return treated

def _ctcp_response(sndr, msg):
    return response.Response(sndr, msg, ctcp=True)


def _help_msg(sndr, modules, cmd):
    """Parse and response to help messages"""
    res = response.Response(sndr)
    if len(cmd) > 1:
        if cmd[1] in modules:
            if len(cmd) > 2:
                if hasattr(modules[cmd[1]], "HELP_cmd"):
                    res.append_message(modules[cmd[1]].HELP_cmd(cmd[2]))
                else:
                    res.append_message("No help for command %s in module %s" % (cmd[2], cmd[1]))
            elif hasattr(modules[cmd[1]], "help_full"):
                res.append_message(modules[cmd[1]].help_full())
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
                           message=["\x03\x02%s\x03\x02 (%s)" % (im, modules[im].__doc__) for im in modules if modules[im].__doc__])
    return res

def hotswap(bak):
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

    import DCC
    imp.reload(DCC)

    import event
    imp.reload(event)

    import hooks
    imp.reload(hooks)

    import importer
    imp.reload(importer)

    import message
    imp.reload(message)

    import prompt.builtins
    imp.reload(prompt.builtins)

    import server
    imp.reload(server)

    import xmlparser
    imp.reload(xmlparser)
    import xmlparser.node
    imp.reload(xmlparser.node)
