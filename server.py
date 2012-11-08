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

import socket
import sys
import threading

class Server(threading.Thread):
    def __init__(self, socket = None):
      self.stop = False
      self.stopping = threading.Event()
      self.s = socket
      self.connected = self.s is not None
      self.closing_event = None

      self.moremessages = dict()

      threading.Thread.__init__(self)

    def isDCC(self, to=None):
        return to is not None and to in self.dcc_clients

    @property
    def ip(self):
        """Convert common IP representation to little-endian integer representation"""
        sum = 0
        if self.node.hasAttribute("ip"):
            ip = self.node["ip"]
        else:
            #TODO: find the external IP
            ip = "0.0.0.0"
        for b in ip.split("."):
            sum = 256 * sum + int(b)
        return sum

    def toIP(self, input):
        """Convert little-endian int to IPv4 adress"""
        ip = ""
        for i in range(0,4):
            mod = input % 256
            ip = "%d.%s" % (mod, ip)
            input = (input - mod) / 256
        return ip[:len(ip) - 1]

    @property
    def id(self):
        """Gives the server identifiant"""
        raise NotImplemented()

    def accepted_channel(self, msg, sender=None):
        return True

    def msg_treated(self, origin):
        """Action done on server when a message was treated"""
        raise NotImplemented()

    def send_response(self, res, origin):
        """Analyse a Response and send it"""
        # TODO: how to send a CTCP message to a different person
        if res.ctcp:
            self.send_ctcp(res.sender, res.get_message())

        elif res.channel is not None and res.channel != self.nick:
            self.send_msg(res.channel, res.get_message())

            if not res.alone:
                if hasattr(self, "send_bot"):
                    self.send_bot("NOMORE %s" % res.channel)
                self.moremessages[res.channel] = res
        elif res.sender is not None:
            self.send_msg_usr(res.sender, res.get_message())

            if not res.alone:
                self.moremessages[res.sender] = res

    def send_ctcp(self, to, msg, cmd="NOTICE", endl="\r\n"):
        """Send a message as CTCP response"""
        if msg is not None and to is not None:
            for line in msg.split("\n"):
                if line != "":
                    self.send_msg_final(to.split("!")[0], "\x01" + line + "\x01", cmd, endl)

    def send_dcc(self, msg, to):
        """Send a message through DCC connection"""
        raise NotImplemented()

    def send_msg_final(self, channel, msg, cmd="PRIVMSG", endl="\r\n"):
        """Send a message without checks or format"""
        raise NotImplemented()

    def send_msg_usr(self, user, msg):
        """Send a message to a user instead of a channel"""
        raise NotImplemented()

    def send_msg(self, channel, msg, cmd="PRIVMSG", endl="\r\n"):
        """Send a message to a channel"""
        if msg is not None:
            for line in msg.split("\n"):
                if line != "":
                    self.send_msg_final(channel, line, cmd, endl)

    def send_msg_verified(self, sender, channel, msg, cmd="PRIVMSG", endl="\r\n"):
        """A more secure way to send messages"""
        raise NotImplemented()

    def send_global(self, msg, cmd="PRIVMSG", endl="\r\n"):
        """Send a message to all channels on this server"""
        raise NotImplemented()

    def disconnect(self):
        """Close the socket with the server"""
        if self.connected:
            self.stop = True
            self.s.shutdown(socket.SHUT_RDWR)

            self.stopping.wait()
            return True
        else:
            return False

    def kill(self):
        """Just stop the main loop, don't close the socket directly"""
        if self.connected:
            self.stop = True
            self.connected = False
            #Send a message in order to close the socket
            self.s.send(("Bye!\r\n" % self.nick).encode ())
            self.stopping.wait()
            return True
        else:
            return False

    def launch(self, receive_action, verb=True):
        """Connect to the server if it is no yet connected"""
        self._receive_action = receive_action
        if not self.connected:
            self.stop = False
            try:
                self.start()
            except RuntimeError:
                pass
        elif verb:
            print ("  Already connected.")

    def treat_msg(self, line, private=False):
        self._receive_action(self, line, private)

    def run(self):
        raise NotImplemented()
