#!/usr/bin/python3
# coding=utf-8

import sys
import signal
import os
import re
from datetime import date
from datetime import datetime
from datetime import timedelta
from xml.dom.minidom import parse

import birthday
import norme
import newyear
import ontime
import watchWebsite

if len(sys.argv) == 1:
    print "This script takes exactly 1 arg: a XML config file"
    sys.exit(1)



class Server:
    def __init__(self, server):
        if server.hasAttribute("server"):
            self.host = server.getAttribute("server")
        else:
            self.host = "localhost"
        if server.hasAttribute("port"):
            self.port = int(server.getAttribute("port"))
        else:
            self.port = 6667
        if server.hasAttribute("password"):
            self.password = server.getAttribute("password")
        else:
            self.password = None

        self.channels = list()
        for channel in server.getElementsByTagName('channel'):
            self.channels.append(channel.getAttribute("name"))

    def launch(self):
        thread.start_new_thread(self.connect, ())

    def accepted_channel(self, channel):
        return (self.channels.find(channel) != -1)

    def read(self):
        readbuffer = "" #Here we store all the messages from server
        while 1:
            readbuffer = readbuffer + self.s.recv(1024) #recieve server messages
            temp = readbuffer.split("\n")
            readbuffer = temp.pop( )

            for line in temp:
                line = line.rstrip() #remove trailing 'rn'

                if line.find('PRIVMSG') != -1: #Call a parsing function
                    complete = line[1:].split(':',1) #Parse the message into useful data
                    info = complete[0].split(' ')
                    msgpart = complete[1]
                    sender = info[0].split('!')
                    if len(msgpart) > 0 and self.accepted_channel(info[2]):
                        parsemsg(info[2], sender[0], msgpart)

                line = line.split()

                if(line[0] == 'PING'): #If server pings then pong
                    self.s.send("PONG %s\r\n" % line[1])

    def parsemsg(self, channel, sender, msg):
        if re.match(".*(norme|coding style).*", msg) is not None and re.match(".*(please|give|obtenir|now|plz|stp|svp|s'il (te|vous) pla.t|check).*", msg) is not None:
            norme.launch (self.s, sender, msg)

        elif msg.find("%s:"%NICK) == 0: #Treat all messages starting with 'nemubot:' as distinct commands
            msgl = msg.lower()
            if re.match(".*(m[' ]?entends?[ -]+tu|h?ear me|ping).*", msgl) is not None:
                self.s.send("PRIVMSG %s :%s: pong\r\n"%(channel, sender))
            elif re.match(".*di[st] (a|à) ([a-zA-Z0-9_]+) (.+)$", msgl) is not None:
                result = re.match(".*di[st] (a|à) ([a-zA-Z0-9_]+) (qu(e |'))?(.+)$", msg)
                self.s.send("PRIVMSG %s :%s: %s\r\n"%(channel, result.group(2), result.group(5)))
            elif re.match(".*di[st] (.+) (a|à) ([a-zA-Z0-9_]+)$", msgl) is not None:
                result = re.match(".*di[st] (.+) (à|a) ([a-zA-Z0-9_]+)$", msg)
                self.s.send("PRIVMSG %s :%s: %s\r\n"%(channel, result.group(3), result.group(1)))
            else:
                if not birthday.parseask(self.s, channel, sender, msgl):
                    return



    def connect(self):
        self.s = socket.socket( ) #Create the socket
        self.s.connect((self.host, self.port)) #Connect to server
        if self.password != None:
            self.s.send("PASS %s\r\n" % self.password)
        self.s.send("NICK %s\r\n" % NICK)
        self.s.send("USER %s %s bla :%s\r\n" % (NICK, self.host, REALNAME))
        #s.send("JOIN %s\r\n" % CHANLIST)
        self.read()

for server in config.getElementsByTagName('server'):
    srv = Server(server)
    srv.launch()

print ("Nemubot ready, I operate on %s. My PID is %i" % (CHANLIST, os.getpid()))
prompt=""
while prompt != "quit":
    prompt=sys.stdin.readlines ()

sys.exit(0)
