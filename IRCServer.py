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

import errno
import os
import socket
import threading
import traceback

from channel import Channel
from DCC import DCC
from hooks import Hook
import message
import server
import xmlparser

class IRCServer(server.Server):
    """Class to interact with an IRC server"""

    def __init__(self, node, nick, owner, realname):
        """Initialize an IRC server

        Arguments:
        node -- server node from XML configuration
        nick -- nick used by the bot on this server
        owner -- nick used by the bot owner on this server
        realname -- string used as realname on this server

        """
        server.Server.__init__(self)

        self.node = node

        self.nick = nick
        self.owner = owner
        self.realname = realname

        # Listen private messages?
        self.listen_nick = True

        self.dcc_clients = dict()

        self.channels = dict()
        for chn in self.node.getNodes("channel"):
            chan = Channel(chn["name"], chn["password"])
            self.channels[chan.name] = chan


    @property
    def host(self):
        """Return the server hostname"""
        if self.node is not None and self.node.hasAttribute("server"):
            return self.node["server"]
        else:
            return "localhost"

    @property
    def port(self):
        """Return the connection port used on this server"""
        if self.node is not None and self.node.hasAttribute("port"):
            return self.node.getInt("port")
        else:
            return "6667"

    @property
    def password(self):
        """Return the password used to connect to this server"""
        if self.node is not None and self.node.hasAttribute("password"):
            return self.node["password"]
        else:
            return None

    @property
    def allow_all(self):
        """If True, treat message from all channels, not only listed one"""
        return (self.node is not None and self.node.hasAttribute("allowall")
                and self.node["allowall"] == "true")

    @property
    def autoconnect(self):
        """Autoconnect the server when added"""
        if self.node is not None and self.node.hasAttribute("autoconnect"):
            value = self.node["autoconnect"].lower()
            return value != "no" and value != "off" and value != "false"
        else:
            return False

    @property
    def id(self):
        """Gives the server identifiant"""
        return self.host + ":" + str(self.port)

    def register_hooks(self):
        self.add_hook(Hook(self.evt_channel, "JOIN"))
        self.add_hook(Hook(self.evt_channel, "PART"))
        self.add_hook(Hook(self.evt_server, "NICK"))
        self.add_hook(Hook(self.evt_server, "QUIT"))
        self.add_hook(Hook(self.evt_channel, "332"))
        self.add_hook(Hook(self.evt_channel, "353"))

    def evt_server(self, msg, srv):
        for chan in self.channels:
            self.channels[chan].treat(msg.cmd, msg)

    def evt_channel(self, msg, srv):
        if msg.channel is not None:
            if msg.channel in self.channels:
                self.channels[msg.channel].treat(msg.cmd, msg)

    def accepted_channel(self, chan, sender = None):
        """Return True if the channel (or the user) is authorized"""
        if self.allow_all:
            return True
        elif self.listen_nick:
            return (chan in self.channels and (sender is None or sender in
                                               self.channels[chan].people)
                    ) or chan == self.nick
        else:
            return chan in self.channels and (sender is None or sender
                                              in self.channels[chan].people)

    def join(self, chan, password=None, force=False):
        """Join a channel"""
        if force or (chan is not None and
                     self.connected and chan not in self.channels):
            self.channels[chan] = Channel(chan, password)
            if password is not None:
                self.s.send(("JOIN %s %s\r\n" % (chan, password)).encode())
            else:
                self.s.send(("JOIN %s\r\n" % chan).encode())
            return True
        else:
            return False

    def leave(self, chan):
        """Leave a channel"""
        if chan is not None and self.connected and chan in self.channels:
            if isinstance(chan, list):
                for c in chan:
                    self.leave(c)
            else:
                self.s.send(("PART %s\r\n" % self.channels[chan].name).encode())
                del self.channels[chan]
            return True
        else:
            return False

# Main loop
    def run(self):
        if not self.connected:
            self.s = socket.socket() #Create the socket
            try:
                self.s.connect((self.host, self.port)) #Connect to server
            except socket.error as e:
                self.s = None
                print ("\033[1;31mError:\033[0m Unable to connect to %s:%d: %s"
                       % (self.host, self.port, os.strerror(e.errno)))
                return
            self.stopping.clear()

            if self.password != None:
                self.s.send(b"PASS " + self.password.encode () + b"\r\n")
            self.s.send(("NICK %s\r\n" % self.nick).encode ())
            self.s.send(("USER %s %s bla :%s\r\n" % (self.nick, self.host,
                                                     self.realname)).encode())
            raw = self.s.recv(1024)
            if not raw:
                print ("Unable to connect to %s:%d" % (self.host, self.port))
                return
            self.connected = True
            print ("Connection to %s:%d completed" % (self.host, self.port))

            if len(self.channels) > 0:
                for chn in self.channels.keys():
                    self.join(self.channels[chn].name,
                              self.channels[chn].password, force=True)


        readbuffer = b'' #Here we store all the messages from server
        while not self.stop:
            readbuffer = readbuffer + raw
            temp = readbuffer.split(b'\n')
            readbuffer = temp.pop()

            for line in temp:
                self.treat_msg(line)
            raw = self.s.recv(1024) #recieve server messages

        if self.connected:
            self.s.close()
            self.connected = False
            print ("Server `%s' successfully stopped." % self.id)
        self.stopping.set()
        # Rearm Thread
        threading.Thread.__init__(self)


# Overwritted methods

    def disconnect(self):
        """Close the socket with the server and all DCC client connections"""
        #Close all DCC connection
        clts = [c for c in self.dcc_clients]
        for clt in clts:
            self.dcc_clients[clt].disconnect()
        return server.Server.disconnect(self)



# Abstract methods

    def send_pong(self, cnt):
        """Send a PONG command to the server with argument cnt"""
        self.s.send(("PONG %s\r\n" % cnt).encode())

    def msg_treated(self, origin):
        """Do nothing; here for implement abstract class"""
        pass

    def send_dcc(self, msg, to):
        """Send a message through DCC connection"""
        if msg is not None and to is not None:
            realname = to.split("!")[1]
            if realname not in self.dcc_clients.keys():
                d = DCC(self, to)
                self.dcc_clients[realname] = d
            self.dcc_clients[realname].send_dcc(msg)

    def send_msg_final(self, channel, line, cmd="PRIVMSG", endl="\r\n"):
        """Send a message without checks or format"""
        #TODO: add something for post message treatment here
        if channel == self.nick:
            print ("\033[1;35mWarning:\033[0m Nemubot talks to himself: %s" % msg)
            traceback.print_stack()
        if line is not None and channel is not None:
                    if self.s is None:
                        print ("\033[1;35mWarning:\033[0m Attempt to send message on a non connected server: %s: %s" % (self.id, line))
                        traceback.print_stack()
                    elif len(line) < 442:
                        self.s.send (("%s %s :%s%s" % (cmd, channel, line, endl)).encode ())
                    else:
                        print ("\033[1;35mWarning:\033[0m Message truncated due to size (%d ; max : 442) : %s" % (len(line), line))
                        traceback.print_stack()
                        self.s.send (("%s %s :%s%s" % (cmd, channel, line[0:442]+"...", endl)).encode ())

    def send_msg_usr(self, user, msg):
        """Send a message to a user instead of a channel"""
        if user is not None and user[0] != "#":
            realname = user.split("!")[1]
            if realname in self.dcc_clients or user in self.dcc_clients:
                self.send_dcc(msg, user)
            else:
                for line in msg.split("\n"):
                    if line != "":
                        self.send_msg_final(user.split('!')[0], msg)

    def send_msg(self, channel, msg, cmd="PRIVMSG", endl="\r\n"):
        """Send a message to a channel"""
        if self.accepted_channel(channel):
            server.Server.send_msg(self, channel, msg, cmd, endl)

    def send_msg_verified(self, sender, channel, msg, cmd = "PRIVMSG", endl = "\r\n"):
        """Send a message to a channel, only if the source user is on this channel too"""
        if self.accepted_channel(channel, sender):
            self.send_msg_final(channel, msg, cmd, endl)

    def send_global(self, msg, cmd="PRIVMSG", endl="\r\n"):
        """Send a message to all channels on this server"""
        for channel in self.channels.keys():
            self.send_msg(channel, msg, cmd, endl)
