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

import bot
from message import Message
import server
from server.socket import SocketServer

class IRCServer(SocketServer):

    def __init__(self, node, nick, owner, realname):
        SocketServer.__init__(self,
                              node["host"],
                              node["port"],
                              node["password"],
                              node.hasAttribute("ssl") and node["ssl"].lower() == "true")

        self.nick     = nick
        self.owner    = owner
        self.realname = realname
        self.id       = nick + "@" + node["host"] + ":" + node["port"]


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
            return _ctcp_response(msg.sender,
                                  " ".join(self.ctcp_capabilities.keys()))

        def _ctcp_dcc(msg):
            """Response to DCC CTCP message"""
            try:
                ip = srv.toIP(int(msg.cmds[3]))
                port = int(msg.cmds[4])
                conn = DCC(srv, msg.sender)
            except:
                return _ctcp_response(msg.sender, "ERRMSG invalid parameters provided as DCC CTCP request")

            self.logger.info("Receive DCC connection request from %s to %s:%d", conn.sender, ip, port)

            if conn.accept_user(ip, port):
                srv.dcc_clients[conn.sender] = conn
                conn.send_dcc("Hello %s!" % conn.nick)
            else:
                self.logger.error("DCC: unable to connect to %s:%d", ip, port)
                return _ctcp_response(msg.sender, "ERRMSG unable to connect to %s:%d" % (ip, port))

        self.ctcp_capabilities["ACTION"] = lambda msg: print ("ACTION receive: %s" % msg.text)
        self.ctcp_capabilities["CLIENTINFO"] = _ctcp_clientinfo
        #self.ctcp_capabilities["DCC"] = _ctcp_dcc
        self.ctcp_capabilities["FINGER"] = lambda msg: _ctcp_response(
            msg.sender, "VERSION nemubot v%s" % bot.__version__)
        self.ctcp_capabilities["NEMUBOT"] = lambda msg: _ctcp_response(
            msg.sender, "NEMUBOT %s" % bot.__version__)
        self.ctcp_capabilities["PING"] = lambda msg: _ctcp_response(
            msg.sender, "PING %s" % " ".join(msg.cmds[1:]))
        self.ctcp_capabilities["SOURCE"] = lambda msg: _ctcp_response(
            msg.sender, "SOURCE https://github.com/nemunaire/nemubot")
        self.ctcp_capabilities["TIME"] = lambda msg: _ctcp_response(
            msg.sender, "TIME %s" % (datetime.now()))
        self.ctcp_capabilities["USERINFO"] = lambda msg: _ctcp_response(
            msg.sender, "USERINFO %s" % self.realname)
        self.ctcp_capabilities["VERSION"] = lambda msg: _ctcp_response(
            msg.sender, "VERSION nemubot v%s" % bot.__version__)

        self.logger.debug("CTCP capabilities setup: %s", ", ".join(self.ctcp_capabilities))

        # Register hooks on some IRC CMD
        self.hookscmd = dict()

        def _on_ping(msg):
            self.write("%s :%s" % ("PONG", msg.params[0]))
        self.hookscmd["PING"] = _on_ping

        def _on_connect(msg):
            # First, JOIN some channels
            for chn in node.getNodes("channel"):
                if chn["password"] is not None:
                    self.write("JOIN %s %s" % (chn["name"], chn["password"]))
                else:
                    self.write("JOIN %s" % chn["name"])
        self.hookscmd["001"] = _on_connect

        def _on_error(msg):
            self.close()
        self.hookscmd["ERROR"] = _on_error

        def _on_cap(msg):
            if len(msg.params) != 3 or msg.params[1] != "LS":
                return
            server_caps = msg.params[2].split(" ")
            for cap in self.capabilities:
                if cap not in server_caps:
                    self.capabilities.remove(cap)
            if len(self.capabilities) > 0:
                self.write("CAP REQ :" + " ".join(self.capabilities))
            self.write("CAP END")
        self.hookscmd["CAP"] = _on_cap


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

    def send_response(self, res):
        if type(res.channel) != list:
            res.channel = [ res.channel ]
        for channel in res.channel:
            if channel is not None and channel != self.nick:
                self.write("%s %s :%s" % ("PRIVMSG", channel, res.get_message()))
            else:
                channel = res.sender.split("!")[0]
                self.write("%s %s :%s" % ("NOTICE" if res.is_ctcp else "PRIVMSG", channel, res.get_message()))


    def _close(self):
        if self.socket is not None: self.write("QUIT")
        return SocketServer._close(self)

    def read(self):
        for line in SocketServer.read(self):
            msg = Message(line, datetime.now())

            if msg.cmd in self.hookscmd:
                self.hookscmd[msg.cmd](msg)

            elif msg.cmd == "PRIVMSG" and msg.is_ctcp:
                if msg.cmds[0] in self.ctcp_capabilities:
                    res = self.ctcp_capabilities[msg.cmds[0]](msg)
                else:
                    res = _ctcp_response(msg.sender, "ERRMSG Unknown or unimplemented CTCP request")
                if res is not None:
                    self.send_response(res)

            else:
                yield msg


from response import Response

def _ctcp_response(sndr, msg):
    return Response(sndr, msg, ctcp=True)
