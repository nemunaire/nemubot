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
import traceback

import channel
import DCC
import message
import xmlparser

class Server(threading.Thread):
    def __init__(self, node, nick, owner, realname, socket = None):
      self.stop = False
      self.stopping = threading.Event()
      self.nick = nick
      self.owner = owner
      self.realname = realname
      self.s = socket
      self.connected = self.s is not None
      self.node = node

      self.listen_nick = True

      self.dcc_clients = dict()

      self.channels = dict()
      for chn in node.getNodes("channel"):
        chan = channel.Channel(chn, self)
        self.channels[chan.name] = chan

      self.moremessages = dict()

      threading.Thread.__init__(self)

    def isDCC(self, to=None):
        return to is not None and to in self.dcc_clients

    @property
    def host(self):
      if self.node.hasAttribute("server"):
        return self.node["server"]
      else:
        return "localhost"

    @property
    def port(self):
      if self.node.hasAttribute("port"):
        return self.node.getInt("port")
      else:
        return "6667"

    @property
    def password(self):
      if self.node.hasAttribute("password"):
        return self.node["password"]
      else:
        return None

    @property
    def ip(self):
        """Convert common IP representation to little-endian integer representation"""
        sum = 0
        if self.node.hasAttribute("ip"):
            for b in self.node["ip"].split("."):
                sum = 256 * sum + int(b)
        else:
            #TODO: find the external IP
            pass
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
    def autoconnect(self):
      if self.node.hasAttribute("autoconnect"):
        value = self.node["autoconnect"].lower()
        return value != "no" and value != "off" and value != "false"
      else:
        return False

    @property
    def id(self):
        return self.host + ":" + str(self.port)

    def send_pong(self, cnt):
        self.s.send(("PONG %s\r\n" % cnt).encode ())

    def msg_treated(self, origin):
        """Do nothing, here for implement abstract class"""
        pass

    def send_response(self, res, origin):
        if res.channel is not None and res.channel != self.nick:
            self.send_msg(res.channel, res.get_message())

            if not res.alone:
                self.moremessages[res.channel] = res
        elif res.sender is not None:
            self.send_msg_usr(res.sender, res.get_message())

            if not res.alone:
                self.moremessages[res.sender] = res

    def send_ctcp(self, to, msg, cmd = "NOTICE", endl = "\r\n"):
      """Send a message as CTCP response"""
      if msg is not None and to is not None:
        for line in msg.split("\n"):
          if line != "":
            self.s.send (("%s %s :\x01%s\x01%s" % (cmd, to.split("!")[0], line, endl)).encode ())

    def send_dcc(self, msg, to):
      """Send a message through DCC connection"""
      if msg is not None and to is not None:
        realname = to.split("!")[1]
        if realname not in self.dcc_clients.keys():
          d = dcc.DCC(self, to)
          self.dcc_clients[realname] = d
        self.dcc_clients[realname].send_dcc(msg)


    def send_msg_final(self, channel, msg, cmd = "PRIVMSG", endl = "\r\n"):
        """Send a message without checks"""
        if channel == self.nick:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            print ("\033[1;35mWarning:\033[0m Nemubot talks to himself: %s" % msg)
        if msg is not None and channel is not None:
            for line in msg.split("\n"):
                if line != "":
                    if len(line) < 442:
                        self.s.send (("%s %s :%s%s" % (cmd, channel, line, endl)).encode ())
                    else:
                        self.s.send (("%s %s :%s%s" % (cmd, channel, line[0:442]+"...", endl)).encode ())

    def send_msg_usr(self, user, msg):
        """Send a message to a user instead of a channel"""
        if user is not None and user[0] != "#":
            realname = user.split("!")[1]
            if realname in self.dcc_clients:
                self.send_dcc(msg, user)
            else:
                self.send_msg_final(user.split('!')[0], msg)

    def send_msg(self, channel, msg, cmd = "PRIVMSG", endl = "\r\n"):
        """Send a message to a channel"""
        if self.accepted_channel(channel):
            self.send_msg_final(channel, msg, cmd, endl)

    def send_msg_verified(self, sender, channel, msg, cmd = "PRIVMSG", endl = "\r\n"):
        """Send a message to a channel, only if the source user is on this channel too"""
        if self.accepted_channel(channel, sender):
            self.send_msg_final(channel, msg, cmd, endl)

    def send_global(self, msg, cmd = "PRIVMSG", endl = "\r\n"):
        """Send a message to all channels on this server"""
        for channel in self.channels.keys():
            self.send_msg(channel, msg, cmd, endl)


    def accepted_channel(self, chan, sender = None):
        """Return True if the channel (or the user) is authorized"""
        if self.listen_nick:
            return (chan in self.channels and (sender is None or sender in
                                               self.channels[chan].people)
                    ) or chan == self.nick
        else:
            return chan in self.channels and (sender is None or sender
                                              in self.channels[chan].people)

    def disconnect(self):
        """Close the socket with the server and all DCC client connections"""
        if self.connected:
            self.stop = True
            self.s.shutdown(socket.SHUT_RDWR)

            #Close all DCC connection
            for clt in self.dcc_clients:
                self.dcc_clients[clt].disconnect()

            self.stopping.wait()
            return True
        else:
            return False

    def kill(self):
        if self.connected:
            self.stop = True
            self.connected = False
            #Send a message in order to close the socket
            self.s.send(("WHO %s\r\n" % self.nick).encode ())
            self.stopping.wait()
            return True
        else:
            return False

    def join(self, chan, password = None):
        """Join a channel"""
        if chan is not None and self.connected and chan not in self.channels:
            chn = xmlparser.module_state.ModuleState("channel")
            chn["name"] = chan
            chn["password"] = password
            self.node.addChild(chn)
            self.channels[chan] = channel.Channel(chn, self)
            if password is not None:
                self.s.send(("JOIN %s %s\r\n" % (chan, password)).encode ())
            else:
                self.s.send(("JOIN %s\r\n" % chan).encode ())
            return True
        else:
            return False

    def leave(self, chan):
        """Leave a channel"""
        if chan is not None and self.connected and chan in self.channels:
            self.s.send(("PART %s\r\n" % self.channels[chan].name).encode ())
            del self.channels[chan]
            return True
        else:
            return False

    def launch(self, context, verb=True):
        """Connect to the server if it is no yet connected"""
        self.context = context
        if not self.connected:
            self.stop = False
            self.start()
        elif verb:
            print ("  Already connected.")

    def treat_msg(self, line, private = False):
        self.context.receive_message(self, line, private)

    def run(self):
      if not self.connected:
          self.s = socket.socket() #Create the socket
          self.s.connect((self.host, self.port)) #Connect to server
          self.stopping.clear()
          self.connected = True

          if self.password != None:
              self.s.send(b"PASS " + self.password.encode () + b"\r\n")
          self.s.send(("NICK %s\r\n" % self.nick).encode ())
          self.s.send(("USER %s %s bla :%s\r\n" % (self.nick, self.host,
                                                   self.realname)).encode ())
          print ("Connection to %s:%d completed" % (self.host, self.port))

          if len(self.channels) > 0:
              for chn in self.channels.keys():
                  if self.channels[chn].password is not None:
                      self.s.send(("JOIN %s %s\r\n" % (self.channels[chn].name,
                                       self.channels[chn].password)).encode ())
                  else:
                      self.s.send(("JOIN %s\r\n" %
                                   self.channels[chn].name).encode ())
          print ("Listen to channels: %s" % ' '.join (self.channels.keys()))

      readbuffer = b'' #Here we store all the messages from server
      while not self.stop:
        raw = self.s.recv(1024) #recieve server messages
        if not raw:
          break
        readbuffer = readbuffer + raw
        temp = readbuffer.split(b'\n')
        readbuffer = temp.pop()

        for line in temp:
          self.treat_msg(line)

      if self.connected:
          self.s.close()
          self.connected = False
          print ("Server `%s' successfully stopped." % self.id)
      self.stopping.set()
      #Rearm Thread
      threading.Thread.__init__(self)
