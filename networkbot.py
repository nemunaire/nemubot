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

import random
import shlex

from botcaps import BotCaps
from DCC import DCC

class NetworkBot:
    def __init__(self, context, srv, dest, dcc=None):
        self.context = context
        self.srv = srv
        self.dcc = dcc
        self.dest = dest
        self.infos = None

        self.my_tag = random.randint(0,255)
        self.inc_tag = 0
        self.tags = dict()

    @property
    def sender(self):
        if self.dcc is not None:
            return self.dcc.sender
        return None

    @property
    def nick(self):
        if self.dcc is not None:
            return self.dcc.nick
        return None

    @property
    def realname(self):
        if self.dcc is not None:
            return self.dcc.realname
        return None

    def send_cmd(self, cmd, data=None):
        """Create a tag and send the command"""
        # First, define a tag
        self.inc_tag = (self.inc_out + 1) % 256
        while self.inc_tag in self.tags:
            self.inc_tag = (self.inc_out + 1) % 256
        tag = ("%c%c" % (self.my_tag, self.inc_tag)).encode()

        if data is not None:
            self.tags[tag] = data
        else:
            self.tags[tag] = cmd

        # Send the command with the tag
        self.send_response(tag, cmd)

    def send_response(self, tag, msg):
        """Send a response with a tag"""
        for line in msg.split("\n"):
            self.dcc.send_dcc_raw(tag + b' ' + line.encode())

    def send_ack(self, tag):
        """Acknowledge a command"""
        if tag in self.tags:
            del self.tags[tag]
        self.send_response(tag, "ACK")

    def connect(self):
        """Making the connexion with dest through srv"""
        if self.dcc is None:
            self.dcc = DCC(self.srv, self.dest)
            self.dcc.treatement = self.hello
            self.dcc.send_dcc("NEMUBOT###")

    def disconnect(self, reason=""):
        """Close the connection and remove the bot from network list"""
        del self.context.network[self.dcc.id]
        self.dcc.send_dcc("DISCONNECT :%s" % reason)
        self.dcc.disconnect()

    def hello(self, line):
        if line == b'NEMUBOT###':
            self.dcc.treatement = self.treat_msg
            self.send_cmd("MYTAG %c" % self.my_tag)
            self.send_cmd("FETCH")
        elif line != b'Hello ' + self.srv.nick.encode() + b'!':
            self.disconnect("Sorry, I think you were a bot")

    def treat_msg(self, line, cmd=None):
        print (line)
        words = line.split(b' ')

        # Ignore invalid commands
        if len(words) >= 2:
            tag = words[0]
            cmd = words[1]
            if len(words) > 2:
                args = shlex.split(line[len(tag) + len(cmd) + 2:].decode())
            else:
                args = list()

            # Parse
            if cmd == b'ACK':
                if tag in self.tags:
                    del self.tags[tag]

            elif cmd == b'MYTAG' and len(args) > 0:
                while args[0] == self.my_tag:
                    self.my_tag = random.randint(0,255)
                self.send_ack(tag)
