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

import server
from server.socket import SocketServer

class IRCServer(SocketServer):

    def __init__(self, node, nick, owner, realname):
        SocketServer.__init__(self,
                              node["host"],
                              node["port"],
                              node["password"],
                              node.hasAttribute("ssl") and node["ssl"].lower() == "true")

        self.nick = nick
        self.owner = owner
        self.realname = realname
        self.id = "TODO"

        if node.hasAttribute("caps"):
            if node["caps"].lower() == "no":
                self.capabilities = None
            else:
                self.capabilities = node["caps"].split(",")
        else:
            self.capabilities = list()

        def _on_connect():
            # First, JOIN some channels
            for chn in node.getNodes("channel"):
                if chn["password"] is not None:
                    self.write("JOIN %s %s" % (chn["name"], chn["password"]))
                else:
                    self.write("JOIN %s" % chn["name"])
        self._on_connect = _on_connect

        def _on_caps_ls(msg):
            if len(msg.params) != 3 or msg.params[1] != "LS":
                return False
            server_caps = msg.params[2].split(" ")
            for cap in self.capabilities:
                if cap not in server_caps:
                    self.capabilities.remove(cap)
            if len(self.capabilities) > 0:
                self.write("CAP REQ :" + " ".join(self.capabilities))
            self.write("CAP END")
        self._on_caps_ls = _on_caps_ls


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
