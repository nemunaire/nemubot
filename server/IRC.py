# -*- coding: utf-8 -*-

# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2014  nemunaire
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
import re
import shlex

import bot
from channel import Channel
from message import Message
import server
from server.socket import SocketServer

class IRCServer(SocketServer):

    def __init__(self, node, nick, owner, realname):
        self.id       = nick + "@" + node["host"] + ":" + node["port"]
        SocketServer.__init__(self,
                              node["host"],
                              node["port"],
                              node["password"],
                              node.hasAttribute("ssl") and node["ssl"].lower() == "true")

        self.nick     = nick
        self.owner    = owner
        self.realname = realname

        #Keep a list of connected channels
        self.channels = dict()

        if node.hasAttribute("caps"):
            if node["caps"].lower() == "no":
                self.capabilities = None
            else:
                self.capabilities = node["caps"].split(",")
        else:
            self.capabilities = list()

        # Register CTCP capabilities
        self.ctcp_capabilities = dict()

        def _ctcp_clientinfo(msg):
            """Response to CLIENTINFO CTCP message"""
            return _ctcp_response(" ".join(self.ctcp_capabilities.keys()))

        def _ctcp_dcc(msg):
            """Response to DCC CTCP message"""
            try:
                ip = srv.toIP(int(msg.cmds[3]))
                port = int(msg.cmds[4])
                conn = DCC(srv, msg.sender)
            except:
                return _ctcp_response("ERRMSG invalid parameters provided as DCC CTCP request")

            self.logger.info("Receive DCC connection request from %s to %s:%d", conn.sender, ip, port)

            if conn.accept_user(ip, port):
                srv.dcc_clients[conn.sender] = conn
                conn.send_dcc("Hello %s!" % conn.nick)
            else:
                self.logger.error("DCC: unable to connect to %s:%d", ip, port)
                return _ctcp_response("ERRMSG unable to connect to %s:%d" % (ip, port))

        self.ctcp_capabilities["ACTION"] = lambda msg: print ("ACTION receive: %s" % msg.text)
        self.ctcp_capabilities["CLIENTINFO"] = _ctcp_clientinfo
        #self.ctcp_capabilities["DCC"] = _ctcp_dcc
        self.ctcp_capabilities["FINGER"] = lambda msg: _ctcp_response(
            "VERSION nemubot v%s" % bot.__version__)
        self.ctcp_capabilities["NEMUBOT"] = lambda msg: _ctcp_response(
            "NEMUBOT %s" % bot.__version__)
        self.ctcp_capabilities["PING"] = lambda msg: _ctcp_response(
            "PING %s" % " ".join(msg.cmds[1:]))
        self.ctcp_capabilities["SOURCE"] = lambda msg: _ctcp_response(
            "SOURCE https://github.com/nemunaire/nemubot")
        self.ctcp_capabilities["TIME"] = lambda msg: _ctcp_response(
            "TIME %s" % (datetime.now()))
        self.ctcp_capabilities["USERINFO"] = lambda msg: _ctcp_response(
            "USERINFO %s" % self.realname)
        self.ctcp_capabilities["VERSION"] = lambda msg: _ctcp_response(
            "VERSION nemubot v%s" % bot.__version__)

        self.logger.debug("CTCP capabilities setup: %s", ", ".join(self.ctcp_capabilities))

        # Register hooks on some IRC CMD
        self.hookscmd = dict()

        # Respond to PING
        def _on_ping(msg):
            self.write(b"PONG :" + msg.params[0])
        self.hookscmd["PING"] = _on_ping

        # Respond to 001
        def _on_connect(msg):
            # First, JOIN some channels
            for chn in node.getNodes("channel"):
                if chn["password"] is not None:
                    self.write("JOIN %s %s" % (chn["name"], chn["password"]))
                else:
                    self.write("JOIN %s" % chn["name"])
        self.hookscmd["001"] = _on_connect

        # Respond to ERROR
        def _on_error(msg):
            self.close()
        self.hookscmd["ERROR"] = _on_error

        # Respond to CAP
        def _on_cap(msg):
            if len(msg.params) != 3 or msg.params[1] != b"LS":
                return
            server_caps = msg.params[2].decode().split(" ")
            for cap in self.capabilities:
                if cap not in server_caps:
                    self.capabilities.remove(cap)
            if len(self.capabilities) > 0:
                self.write("CAP REQ :" + " ".join(self.capabilities))
            self.write("CAP END")
        self.hookscmd["CAP"] = _on_cap

        # Respond to JOIN
        def _on_join(msg):
            if len(msg.params) == 0: return

            for chname in msg.params[0].split(b","):
                # Register the channel
                chan = Channel(msg.decode(chname))
                self.channels[chname] = chan
        self.hookscmd["JOIN"] = _on_join
        # Respond to PART
        def _on_part(msg):
            if len(msg.params) != 1 and len(msg.params) != 2: return

            for chname in msg.params[0].split(b","):
                if chname in self.channels:
                    if msg.nick == self.nick:
                        del self.channels[chname]
                    elif msg.nick in self.channels[chname].people:
                        del self.channels[chname].people[msg.nick]
        self.hookscmd["PART"] = _on_part
        # Respond to 331/RPL_NOTOPIC,332/RPL_TOPIC,TOPIC
        def _on_topic(msg):
            if len(msg.params) != 1 and len(msg.params) != 2: return
            if msg.params[0] in self.channels:
                if len(msg.params) == 1 or len(msg.params[1]) == 0:
                    self.channels[msg.params[0]].topic = None
                else:
                    self.channels[msg.params[0]].topic = msg.decode(msg.params[1])
        self.hookscmd["331"] = _on_topic
        self.hookscmd["332"] = _on_topic
        self.hookscmd["TOPIC"] = _on_topic
        # Respond to 353/RPL_NAMREPLY
        def _on_353(msg):
            if len(msg.params) == 3: msg.params.pop(0) # 353: like RFC 1459
            if len(msg.params) != 2: return
            if msg.params[0] in self.channels:
                for nk in msg.decode(msg.params[1]).split(" "):
                    res = re.match("^(?P<level>[^a-zA-Z[\]\\`_^{|}])(?P<nickname>[a-zA-Z[\]\\`_^{|}][a-zA-Z0-9[\]\\`_^{|}-]*)$")
                    self.channels[msg.params[0]].people[res.group("nickname")] = res.group("level")
        self.hookscmd["353"] = _on_353


    def _open(self):
        if SocketServer._open(self):
            if self.password is not None:
                self.write("PASS :" + self.password)
            if self.capabilities is not None:
                self.write("CAP LS")
            self.write("NICK :" + self.nick)
            self.write("USER %s %s bla :%s" % (self.nick, self.host, self.realname))
            return True
        return False

    def _close(self):
        if self.socket is not None: self.write("QUIT")
        return SocketServer._close(self)

    def read(self):
        for line in SocketServer.read(self):
            msg = IRCMessage(line, datetime.now())

            if msg.cmd in self.hookscmd:
                self.hookscmd[msg.cmd](msg)

            else:
                mes = msg.to_message()
                mes.raw = msg.raw

                if hasattr(mes, "receivers"):
                    # Private message: prepare response
                    for i in range(len(mes.receivers)):
                        if mes.receivers[i] == self.nick:
                            mes.receivers[i] = mes.nick

                if (mes.cmd == "PRIVMSG" or mes.cmd == "NOTICE") and mes.is_ctcp:
                    if mes.cmds[0] in self.ctcp_capabilities:
                        res = self.ctcp_capabilities[mes.cmds[0]](mes)
                    else:
                        res = _ctcp_response("ERRMSG Unknown or unimplemented CTCP request")
                    if res is not None:
                        res = res % mes.nick
                        self.write(res)

                else:
                    yield mes


def _ctcp_response(msg):
    return "NOTICE %%s :\x01%s\x01" % msg


mgx = re.compile(b'''^(?:@(?P<tags>[^ ]+)\ )?
                      (?::(?P<prefix>
                         (?P<nick>[^!@ ]+)
                         (?: !(?P<user>[^@ ]+))?
                         (?:@(?P<host>[^ ]+))?
                      )\ )?
                      (?P<command>(?:[a-zA-Z]+|[0-9]{3}))
                      (?P<params>(?:\ [^:][^ ]*)*)(?:\ :(?P<trailing>.*))?
                 $''', re.X)

class IRCMessage:

    def __init__(self, raw, timestamp):
        self.raw = raw
        self.tags = { 'time': timestamp }
        self.params = list()

        p = mgx.match(raw.rstrip())

        if p is None:
            raise Exception("Not a valid IRC message: %s" % raw)

        # Parse tags if exists: @aaa=bbb;ccc;example.com/ddd=eee
        if p.group("tags"):
            for tgs in self.decode(p.group("tags")).split(';'):
                tag = tgs.split('=')
                if len(tag) > 1:
                    self.add_tag(tag[0], tag[1])
                else:
                    self.add_tag(tag[0])

        # Parse prefix if exists: :nick!user@host.com
        self.prefix = self.decode(p.group("prefix"))
        self.nick   = self.decode(p.group("nick"))
        self.user   = self.decode(p.group("user"))
        self.host   = self.decode(p.group("host"))

        # Parse command
        self.cmd = self.decode(p.group("command"))

        # Parse params
        if p.group("params") is not None:
            for param in p.group("params").strip().split(b' '):
                self.params.append(param)

        if p.group("trailing") is not None:
            self.params.append(p.group("trailing"))


    def add_tag(self, key, value=None):
        """Add an IRCv3.2 Message Tags"""
        # Treat special tags
        if key == "time":
            # TODO: this is UTC timezone, nemubot works with local timezone
            value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")

        # Store tag
        self.tags[key] = value


    def decode(self, s):
        """Decode the content string usign a specific encoding"""
        if isinstance(s, bytes):
            try:
                s = s.decode()
            except UnicodeDecodeError:
                #TODO: use encoding from config file
                s = s.decode('utf-8', 'replace')
        return s


    def to_message(self):
        return Message(self)

    def to_irc_string(self, client=True):
        res = ";".join(["@%s=%s" % (k,v) for k, v in self.tags.items()])

        if not client: res += " :%s!%s@%s" % (self.nick, self.user, self.host)

        res += " " + self.cmd

        if len(self.params) > 0:

            if len(self.params) > 1:
                res += " " + " ".join(self.params[:-1])
            res += " :" + self.params[-1]

        return res
