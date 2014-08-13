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

import imp
import os
import re
import socket
import sys
import time
import threading
import traceback

import message
import server

#Store all used ports
PORTS = list()

class DCC(server.Server):
    def __init__(self, srv, dest, socket=None):
        server.Server.__init__(self)

        self.error = False # An error has occur, closing the connection?
        self.messages = list() # Message queued before connexion

        # Informations about the sender
        self.sender = dest
        if self.sender is not None:
            self.nick = (self.sender.split('!'))[0]
            if self.nick != self.sender:
                self.realname = (self.sender.split('!'))[1]
            else:
                self.realname = self.nick

        # Keep the server
        self.srv = srv
        self.treatement = self.treat_msg

        # Found a port for the connection
        self.port = self.foundPort()

        if self.port is None:
            print ("No more available slot for DCC connection")
            self.setError("Il n'y a plus de place disponible sur le serveur"
                          " pour initialiser une session DCC.")

    def foundPort(self):
        """Found a free port for the connection"""
        for p in range(65432, 65535):
            if p not in PORTS:
                PORTS.append(p)
                return p
        return None

    @property
    def id(self):
        """Gives the server identifiant"""
        return self.srv.id + "/" + self.sender

    def setError(self, msg):
        self.error = True
        self.srv.send_msg_usr(self.sender, msg)

    def accept_user(self, host, port):
        """Accept a DCC connection"""
        self.s = socket.socket()
        try:
            self.s.connect((host, port))
            print ('Accepted user from', host, port, "for", self.sender)
            self.connected = True
            self.stop = False
        except:
            self.connected = False
            self.error = True
            return False
        self.start()
        return True


    def request_user(self, type="CHAT", filename="CHAT", size=""):
        """Create a DCC connection"""
        #Open the port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('', self.port))
        except:
            try:
                self.port = self.foundPort()
                s.bind(('', self.port))
            except:
                self.setError("Une erreur s'est produite durant la tentative"
                              " d'ouverture d'une session DCC.")
                return False
        print ('Listen on', self.port, "for", self.sender)

        #Send CTCP request for DCC
        self.srv.send_ctcp(self.sender,
                           "DCC %s %s %d %d %s" % (type, filename, self.srv.ip,
                                                   self.port, size),
                           "PRIVMSG")

        s.listen(1)
        #Waiting for the client
        (self.s, addr) = s.accept()
        print ('Connected by', addr)
        self.connected = True
        return True

    def send_dcc_raw(self, line):
        self.s.sendall(line + b'\n')

    def send_dcc(self, msg, to = None):
        """If we talk to this user, send a message through this connection
           else, send the message to the server class"""
        if to is None or to == self.sender or to == self.nick:
            if self.error:
                self.srv.send_msg_final(self.nick, msg)
            elif not self.connected or self.s is None:
                try:
                    self.start()
                except RuntimeError:
                    pass
                self.messages.append(msg)
            else:
                for line in msg.split("\n"):
                    self.send_dcc_raw(line.encode())
        else:
            self.srv.send_dcc(msg, to)

    def send_file(self, filename):
        """Send a file over DCC"""
        if os.path.isfile(filename):
            self.messages = filename
            try:
                self.start()
            except RuntimeError:
                pass
        else:
            print("File not found `%s'" % filename)

    def run(self):
        self.stopping.clear()

        # Send file connection
        if not isinstance(self.messages, list):
            self.request_user("SEND",
                              os.path.basename(self.messages),
                              os.path.getsize(self.messages))
            if self.connected:
                with open(self.messages, 'rb') as f:
                    d = f.read(268435456) #Packets size: 256Mo
                    while d:
                        self.s.sendall(d)
                        self.s.recv(4) #The client send a confirmation after each packet
                        d = f.read(268435456) #Packets size: 256Mo

        # Messages connection
        else:
            if not self.connected:
                if not self.request_user():
                    #TODO: do something here
                    return False

            #Start by sending all queued messages
            for mess in self.messages:
                self.send_dcc(mess)

            time.sleep(1)

            readbuffer = b''
            self.nicksize = len(self.srv.nick)
            self.Bnick = self.srv.nick.encode()
            while not self.stop:
                raw = self.s.recv(1024) #recieve server messages
                if not raw:
                    break
                readbuffer = readbuffer + raw
                temp = readbuffer.split(b'\n')
                readbuffer = temp.pop()

                for line in temp:
                    self.treatement(line)

        if self.connected:
            self.s.close()
            self.connected = False

        #Remove from DCC connections server list
        if self.realname in self.srv.dcc_clients:
            del self.srv.dcc_clients[self.realname]

        print ("Closing connection with", self.nick)
        self.stopping.set()
        if self.closing_event is not None:
            self.closing_event()
        #Rearm Thread
        threading.Thread.__init__(self)

    def treat_msg(self, line):
        """Treat a receive message, *can be overwritten*"""
        if line == b'NEMUBOT###':
            bot = self.srv.add_networkbot(self.srv, self.sender, self)
            self.treatement = bot.treat_msg
            self.send_dcc("NEMUBOT###")
        elif (line[:self.nicksize] == self.Bnick and
            line[self.nicksize+1:].strip()[:10] == b'my name is'):
            name = line[self.nicksize+1:].strip()[11:].decode('utf-8',
                                                         'replace')
            if re.match("^[a-zA-Z0-9_-]+$", name):
                if name not in self.srv.dcc_clients:
                    del self.srv.dcc_clients[self.sender]
                    self.nick = name
                    self.sender = self.nick + "!" + self.realname
                    self.srv.dcc_clients[self.realname] = self
                    self.send_dcc("Hi " + self.nick)
                else:
                    self.send_dcc("This nickname is already in use"
                                  ", please choose another one.")
            else:
                self.send_dcc("The name you entered contain"
                              " invalid char.")
        else:
            self.srv.treat_msg(
                (":%s PRIVMSG %s :" % (
                        self.sender,self.srv.nick)).encode() + line,
                True)
