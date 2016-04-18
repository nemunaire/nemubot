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

from datetime import datetime
import re

from nemubot.channel import Channel
from nemubot.message.printer.IRC import IRC as IRCPrinter
from nemubot.server.message.IRC import IRC as IRCMessage
from nemubot.server.socket import SocketServer


class IRC(SocketServer):

    """Concrete implementation of a connexion to an IRC server"""

    def __init__(self, host="localhost", port=6667, ssl=False, owner=None,
                 nick="nemubot", username=None, password=None,
                 realname="Nemubot", encoding="utf-8", caps=None,
                 channels=list(), on_connect=None):
        """Prepare a connection with an IRC server

        Keyword arguments:
        host -- host to join
        port -- port on the host to reach
        ssl -- is this server using a TLS socket
        owner -- bot's owner
        nick -- bot's nick
        username -- the username as sent to server
        password -- if a password is required to connect to the server
        realname -- the bot's realname
        encoding -- the encoding used on the whole server
        caps -- client capabilities to register on the server
        channels -- list of channels to join on connection
        on_connect -- generator to call when connection is done
        """

        self.username = username if username is not None else nick
        self.password = password
        self.nick     = nick
        self.owner    = owner
        self.realname = realname

        self.id       = self.username + "@" + host + ":" + str(port)
        super().__init__(host=host, port=port, ssl=ssl)
        self.printer  = IRCPrinter

        self.encoding = encoding

        # Keep a list of joined channels
        self.channels = dict()

        # Server/client capabilities
        self.capabilities = caps

        # Register CTCP capabilities
        self.ctcp_capabilities = dict()

        def _ctcp_clientinfo(msg, cmds):
            """Response to CLIENTINFO CTCP message"""
            return " ".join(self.ctcp_capabilities.keys())

        def _ctcp_dcc(msg, cmds):
            """Response to DCC CTCP message"""
            try:
                import ipaddress
                ip = ipaddress.ip_address(int(cmds[3]))
                port = int(cmds[4])
                conn = DCC(srv, msg.sender)
            except:
                return "ERRMSG invalid parameters provided as DCC CTCP request"

            self.logger.info("Receive DCC connection request from %s to %s:%d", conn.sender, ip, port)

            if conn.accept_user(ip, port):
                srv.dcc_clients[conn.sender] = conn
                conn.send_dcc("Hello %s!" % conn.nick)
            else:
                self.logger.error("DCC: unable to connect to %s:%d", ip, port)
                return "ERRMSG unable to connect to %s:%d" % (ip, port)

        import nemubot

        self.ctcp_capabilities["ACTION"] = lambda msg, cmds: None
        self.ctcp_capabilities["CLIENTINFO"] = _ctcp_clientinfo
        #self.ctcp_capabilities["DCC"] = _ctcp_dcc
        self.ctcp_capabilities["FINGER"] = lambda msg, cmds: "VERSION nemubot v%s" % nemubot.__version__
        self.ctcp_capabilities["NEMUBOT"] = lambda msg, cmds: "NEMUBOT %s" % nemubot.__version__
        self.ctcp_capabilities["PING"] = lambda msg, cmds: "PING %s" % " ".join(cmds[1:])
        self.ctcp_capabilities["SOURCE"] = lambda msg, cmds: "SOURCE https://github.com/nemunaire/nemubot"
        self.ctcp_capabilities["TIME"] = lambda msg, cmds: "TIME %s" % (datetime.now())
        self.ctcp_capabilities["USERINFO"] = lambda msg, cmds: "USERINFO %s" % self.realname
        self.ctcp_capabilities["VERSION"] = lambda msg, cmds: "VERSION nemubot v%s" % nemubot.__version__

        # TODO: Temporary fix, waiting for hook based CTCP management
        self.ctcp_capabilities["TYPING"] = lambda msg, cmds: None

        self.logger.debug("CTCP capabilities setup: %s", ", ".join(self.ctcp_capabilities))


        # Register hooks on some IRC CMD
        self.hookscmd = dict()

        # Respond to PING
        def _on_ping(msg):
            self.write(b"PONG :" + msg.params[0])
        self.hookscmd["PING"] = _on_ping

        # Respond to 001
        def _on_connect(msg):
            # First, send user defined command
            if on_connect is not None:
                if callable(on_connect):
                    toc = on_connect()
                else:
                    toc = on_connect
                if toc is not None:
                    for oc in toc:
                        self.write(oc)
            # Then, JOIN some channels
            for chn in channels:
                if chn.password:
                    self.write("JOIN %s %s" % (chn.name, chn.password))
                else:
                    self.write("JOIN %s" % chn.name)
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
            if len(msg.params) == 0:
                return

            for chname in msg.decode(msg.params[0]).split(","):
                # Register the channel
                chan = Channel(chname)
                self.channels[chname] = chan
        self.hookscmd["JOIN"] = _on_join
        # Respond to PART
        def _on_part(msg):
            if len(msg.params) != 1 and len(msg.params) != 2:
                return

            for chname in msg.params[0].split(b","):
                if chname in self.channels:
                    if msg.nick == self.nick:
                        del self.channels[chname]
                    elif msg.nick in self.channels[chname].people:
                        del self.channels[chname].people[msg.nick]
        self.hookscmd["PART"] = _on_part
        # Respond to 331/RPL_NOTOPIC,332/RPL_TOPIC,TOPIC
        def _on_topic(msg):
            if len(msg.params) != 1 and len(msg.params) != 2:
                return
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
            if len(msg.params) == 3:
                msg.params.pop(0)  # 353: like RFC 1459
            if len(msg.params) != 2:
                return
            if msg.params[0] in self.channels:
                for nk in msg.decode(msg.params[1]).split(" "):
                    res = re.match("^(?P<level>[^a-zA-Z[\]\\`_^{|}])(?P<nickname>[a-zA-Z[\]\\`_^{|}][a-zA-Z0-9[\]\\`_^{|}-]*)$")
                    self.channels[msg.params[0]].people[res.group("nickname")] = res.group("level")
        self.hookscmd["353"] = _on_353

        # Respond to INVITE
        def _on_invite(msg):
            if len(msg.params) != 2:
                return
            self.write("JOIN " + msg.decode(msg.params[1]))
        self.hookscmd["INVITE"] = _on_invite

        # Respond to ERR_NICKCOLLISION
        def _on_nickcollision(msg):
            self.nick += "_"
            self.write("NICK " + self.nick)
        self.hookscmd["433"] = _on_nickcollision
        self.hookscmd["436"] = _on_nickcollision

        # Handle CTCP requests
        def _on_ctcp(msg):
            if len(msg.params) != 2 or not msg.is_ctcp:
                return
            cmds = msg.decode(msg.params[1][1:len(msg.params[1])-1]).split(' ')
            if cmds[0] in self.ctcp_capabilities:
                res = self.ctcp_capabilities[cmds[0]](msg, cmds)
            else:
                res = "ERRMSG Unknown or unimplemented CTCP request"
            if res is not None:
                self.write("NOTICE %s :\x01%s\x01" % (msg.nick, res))
        self.hookscmd["PRIVMSG"] = _on_ctcp


    # Open/close

    def open(self):
        if super().open():
            if self.password is not None:
                self.write("PASS :" + self.password)
            if self.capabilities is not None:
                self.write("CAP LS")
            self.write("NICK :" + self.nick)
            self.write("USER %s %s bla :%s" % (self.username, self.host, self.realname))
            return True
        return False


    def close(self):
        if not self.closed:
            self.write("QUIT")
        return super().close()


    # Writes: as inherited

    # Read

    def read(self):
        for line in super().read():
            # PING should be handled here, so start parsing here :/
            msg = IRCMessage(line, self.encoding)

            if msg.cmd in self.hookscmd:
                self.hookscmd[msg.cmd](msg)

            yield msg


    def parse(self, msg):
        mes = msg.to_bot_message(self)
        if mes is not None:
            yield mes


    def subparse(self, orig, cnt):
        msg = IRCMessage(("@time=%s :%s!user@host.com PRIVMSG %s :%s" % (orig.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), orig.frm, ",".join(orig.to), cnt)).encode(self.encoding), self.encoding)
        return msg.to_bot_message(self)
