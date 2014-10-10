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

import calendar
from datetime import datetime, timezone
import re
import time
import shlex

from channel import Channel
import message
from message.printer.IRC import IRC as IRCPrinter
from server.socket import SocketServer
import tools

class IRC(SocketServer):

    def __init__(self, owner, nick="nemubot", host="localhost", port=6667,
                 ssl=False, password=None, realname="Nemubot",
                 encoding="utf-8", caps=None, channels=list(),
                 on_connect=None):
        """Prepare a connection with an IRC server

        Keyword arguments:
        owner -- bot's owner
        nick -- bot's nick
        host -- host to join
        port -- port on the host to reach
        ssl -- is this server using a TLS socket
        password -- if a password is required to connect to the server
        realname -- the bot's realname
        encoding -- the encoding used on the whole server
        caps -- client capabilities to register on the server
        channels -- list of channels to join on connection (if a channel is password protected, give a tuple: (channel_name, password))
        on_connect -- generator to call when connection is done
        """

        self.id       = nick + "@" + host + ":" + port
        self.printer  = IRCPrinter
        SocketServer.__init__(self, host=host, port=port, ssl=ssl)

        self.password = password
        self.nick     = nick
        self.owner    = owner
        self.realname = realname

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
                ip = tools.toIP(int(cmds[3]))
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

        import bot

        self.ctcp_capabilities["ACTION"] = lambda msg, cmds: print ("ACTION receive: %s" % cmds)
        self.ctcp_capabilities["CLIENTINFO"] = _ctcp_clientinfo
        #self.ctcp_capabilities["DCC"] = _ctcp_dcc
        self.ctcp_capabilities["FINGER"] = lambda msg, cmds: "VERSION nemubot v%s" % bot.__version__
        self.ctcp_capabilities["NEMUBOT"] = lambda msg, cmds: "NEMUBOT %s" % bot.__version__
        self.ctcp_capabilities["PING"] = lambda msg, cmds: "PING %s" % " ".join(cmds[1:])
        self.ctcp_capabilities["SOURCE"] = lambda msg, cmds: "SOURCE https://github.com/nemunaire/nemubot"
        self.ctcp_capabilities["TIME"] = lambda msg, cmds: "TIME %s" % (datetime.now())
        self.ctcp_capabilities["USERINFO"] = lambda msg, cmds: "USERINFO %s" % self.realname
        self.ctcp_capabilities["VERSION"] = lambda msg, cmds: "VERSION nemubot v%s" % bot.__version__

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
                for oc in on_connect():
                    self.write(oc)
            # Then, JOIN some channels
            for chn in channels:
                if isinstance(chn, tuple):
                    self.write("JOIN %s %s" % chn)
                else:
                    self.write("JOIN %s" % chn)
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

            for chname in msg.decode(msg.params[0]).split(","):
                # Register the channel
                chan = Channel(chname)
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

        # Respond to INVITE
        def _on_invite(msg):
            if len(msg.params) != 2: return
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
            if len(msg.params) != 2 or not msg.is_ctcp: return
            cmds = msg.decode(msg.params[1][1:len(msg.params[1])-1]).split(' ')
            if cmds[0] in self.ctcp_capabilities:
                res = self.ctcp_capabilities[cmds[0]](msg, cmds)
            else:
                res = "ERRMSG Unknown or unimplemented CTCP request"
            if res is not None:
                self.write("NOTICE %s :\x01%s\x01" % (msg.nick, res))
        self.hookscmd["PRIVMSG"] = _on_ctcp


    # Open/close

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
        if self.connected: self.write("QUIT")
        return SocketServer._close(self)


    # Writes: as inherited

    # Read

    def read(self):
        for line in SocketServer.read(self):
            msg = IRCMessage(line, self.encoding)

            if msg.cmd in self.hookscmd:
                self.hookscmd[msg.cmd](msg)

            mes = msg.to_message(self)
            if mes is not None:
                yield mes


# Parsing stuff

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

    """Class responsible for parsing IRC messages"""

    def __init__(self, raw, encoding="utf-8"):
        self.encoding = encoding
        self.tags = { 'time': datetime.now(timezone.utc) }
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
        if p.group("params") is not None and p.group("params") != b'':
            for param in p.group("params").strip().split(b' '):
                self.params.append(param)

        if p.group("trailing") is not None:
            self.params.append(p.group("trailing"))


    def add_tag(self, key, value=None):
        """Add an IRCv3.2 Message Tags

        Arguments:
        key -- tag identifier (unique for the message)
        value -- optional value for the tag
        """

        # Treat special tags
        if key == "time":
            value = datetime.fromtimestamp(calendar.timegm(time.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")), timezone.utc)

        # Store tag
        self.tags[key] = value


    @property
    def is_ctcp(self):
        """Analyze a message, to determine if this is a CTCP one"""
        return self.cmd == "PRIVMSG" and len(self.params) == 2 and len(self.params[1]) > 1 and (self.params[1][0] == 0x01 or self.params[1][1] == 0x01)


    def decode(self, s):
        """Decode the content string usign a specific encoding

        Argument:
        s -- string to decode
        """

        if isinstance(s, bytes):
            try:
                s = s.decode()
            except UnicodeDecodeError:
                s = s.decode(self.encoding, 'replace')
        return s



    def to_irc_string(self, client=True):
        """Pretty print the message to close to original input string

        Keyword argument:
        client -- export as a client-side string if true
        """

        res = ";".join(["@%s=%s" % (k,v if not isinstance(v, datetime) else v.strftime("%Y-%m-%dT%H:%M:%S.%fZ")) for k, v in self.tags.items()])

        if not client: res += " :%s!%s@%s" % (self.nick, self.user, self.host)

        res += " " + self.cmd

        if len(self.params) > 0:

            if len(self.params) > 1:
                res += " " + self.decode(b" ".join(self.params[:-1]))
            res += " :" + self.decode(self.params[-1])

        return res


    def to_message(self, srv):
        """Convert to one of concrete implementation of AbstractMessage

        Argument:
        srv -- the server from the message was received
        """

        if self.cmd == "PRIVMSG" or self.cmd == "NOTICE":

            receivers = self.decode(self.params[0]).split(',')

            common_args = {
                "server": srv.id,
                "date": self.tags["time"],
                "to": receivers,
                "to_response": [r if r != srv.nick else self.nick for r in receivers],
                "frm": self.nick
            }

            # If CTCP, remove 0x01
            if self.is_ctcp:
                text = self.decode(self.params[1][1:len(self.params[1])-1])
            else:
                text = self.decode(self.params[1])

            if text.find(srv.nick) == 0 and len(text) > len(srv.nick) + 2 and text[len(srv.nick)] == ":":
                designated = srv.nick
                text = text[len(srv.nick) + 1:].strip()
            else:
                designated = None

            # Is this a command?
            if len(text) > 1 and text[0] == '!':
                text = text[1:].strip()

                # Split content by words
                try:
                    args = shlex.split(text)
                except ValueError:
                    args = text.split(' ')

                return message.Command(cmd=args[0], args=args[1:], **common_args)

            # Is this an ask for this bot?
            elif designated is not None:
                return message.DirectAsk(designated=designated, message=text, **common_args)

            # Normal message
            else:
                return message.TextMessage(message=text, **common_args)

        return None
