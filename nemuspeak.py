#!/usr/bin/python2.7
# coding=utf-8

import sys
import socket
import string
import os
import re
import subprocess
from datetime import datetime
from datetime import timedelta
from xml.dom.minidom import parse
import thread

if len(sys.argv) == 1:
    print "This script takes exactly 1 arg: a XML config file"
    sys.exit(1)

SMILEY = list()
g_queue = list()
talkEC = 0
stopSpk = 0
lastmsg = []

dom = parse(sys.argv[1])

config = dom.getElementsByTagName('config')[0]

if config.hasAttribute("nick"):
    NICK = config.getAttribute("nick")
else:
    NICK = "bot"
if config.hasAttribute("owner"):
    OWNER = config.getAttribute("owner")
else:
    OWNER = " "
if config.hasAttribute("realname"):
    REALNAME = config.getAttribute("realname")
else:
    REALNAME = OWNER + "'s bot"

for smiley in config.getElementsByTagName('smiley'):
    if smiley.hasAttribute("txt") and smiley.hasAttribute("mood"):
        SMILEY.append((smiley.getAttribute("txt"), smiley.getAttribute("mood")))
print ("%d smileys loaded"%len(SMILEY))

def speak(endstate):
    global lastmsg, g_queue, talkEC, stopSpk
    talkEC = 1
    stopSpk = 0

    if len(lastmsg) < 1:
        lastmsg = g_queue.pop(0)

    while not stopSpk and len(g_queue) > 0:
        msg = g_queue.pop(0)
        lang = "fr"
        sentence = ""
        force = 0

        if force or msg[2] - lastmsg[2] > timedelta(0, 500):
            sentence += "À {0} heure {1} : ".format(msg[2].hour, msg[2].minute)
            force = 1

        if force or msg[0] != lastmsg[0]:
            if msg[0] == OWNER:
                sentence += "En message privé. "
            else:
                sentence += "Sur " + msg[0] + ". "
            force = 1

        action = 0
        if msg[3].find("ACTION ") == 1:
            sentence += msg[1] + " "
            msg[3] = msg[3].replace("ACTION ", "")
            action = 1
        for (txt, mood) in SMILEY:
            if msg[3].find(txt) >= 0:
                sentence += msg[1] + (" %s : "%mood)
                msg[3] = msg[3].replace(txt, "")
                action = 1
                break

        if action == 0 and (force or msg[1] != lastmsg[1]):
            sentence += msg[1] + " dit : "

        if re.match(".*(https?://)?(www\\.)?ycc.fr/[a-z0-9A-Z]+.*", msg[3]) is not None:
            msg[3] = re.sub("(https?://)?(www\\.)?ycc.fr/[a-z0-9A-Z]+", " U.R.L Y.C.C ", msg[3])

        if re.match(".*https?://.*", msg[3]) is not None:
            msg[3] = re.sub(r'https?://[^ ]+', " U.R.L ", msg[3])

        if re.match("^ *[^a-zA-Z0-9 ][a-zA-Z]{2}[^a-zA-Z0-9 ]", msg[3]) is not None:
            if sentence != "":
                intro = subprocess.call(["espeak", "-v", "fr", sentence])
                #intro.wait()

            lang = msg[3][1:3].lower()
            sentence = msg[3][4:]
        else:
            sentence += msg[3]

        spk = subprocess.call(["espeak", "-v", lang, sentence])
        #spk.wait()

        lastmsg = msg

    if not stopSpk:
        talkEC = endstate
    else:
        talkEC = 1


def parsemsg (msg, CHANLIST):
    global g_queue, NICK, stopSpk, talkEC
    complete = msg[1:].split(':',1) #Parse the message into useful data
    info = complete[0].split(' ')
    msgpart = complete[1]
    sender = info[0].split('!')

    #Skip on empty content
    if len(msgpart) <= 0:
        return

    #Bad format, try to fix that
    if len(info) == 1:
        pv = msg.index(" ", msg.index("PRIVMSG") + 9)
        complete = [ msg[1:pv], msg[pv:] ]
        info = complete[0].split(' ')
        msgpart = complete[1].strip()
        if msgpart[0] == ":":
            msgpart = msgpart[1:]
        sender = info[0].split('!')

    if len(CHANLIST) == 0 or CHANLIST.count(info[2]) >= 0 or info[2] == NICK:
        #Treat all messages starting with '`' as command
        if msgpart[0] == '`' and sender[0] == OWNER:
            cmd=msgpart[1:].split(' ')

            if cmd[0] == 'stop':
                print "Bye!"
                sys.exit (0)

            elif cmd[0] == 'speak':
                thread.start_new_thread(speak, (0,))

            elif cmd[0] == 'reset':
                while len(g_queue) > 0:
                    g_queue.pop()

            elif cmd[0] == 'save':
                if talkEC == 0:
                    talkEC = 1
                stopSpk = 1

            elif cmd[0] == 'test':
                parsemsg(":Quelqun!someone@p0m.fr PRIVMSG %s :Ceci est un message de test ;)"%(CHANLIST[0]), CHANLIST)

            elif cmd[0] == 'list':
                print "Currently listened channels:"
                for chan in CHANLIST:
                    print chan
                print "-- "

            elif cmd[0] == 'add' and len(cmd) > 1:
                CHANLIST.append(cmd[1])
                print cmd[1] + " added to listened channels"

            elif cmd[0] == 'del' and len(cmd) > 1:
                if CHANLIST.count(cmd[1]) > 0:
                    CHANLIST.remove(cmd[1])
                    print cmd[1] + " removed from listened channels"
                else:
                    print cmd[1] + " not in listened channels"

        elif sender[0] != OWNER and (len(CHANLIST) == 0 or CHANLIST.count(info[2]) > 0 or info[2] == OWNER):
            g_queue.append([info[2], sender[0], datetime.now(), msgpart])
            if talkEC == 0:
                thread.start_new_thread(speak, (0,))


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

    def read(self):
        readbuffer = "" #Here we store all the messages from server
        while 1:
            readbuffer = readbuffer + self.s.recv(1024) #recieve server messages
            temp = readbuffer.split("\n")
            readbuffer = temp.pop( )

            for line in temp:
                line = line.rstrip() #remove trailing 'rn'

                if line.find('PRIVMSG') != -1: #Call a parsing function
                    parsemsg(unicode(line, encoding='utf-8'), self.channels)

                line = line.split()

                if(line[0] == 'PING'): #If server pings then pong
                    self.s.send("PONG %s\r\n" % line[1])

    def connect(self):
        self.s = socket.socket( ) #Create the socket
        self.s.connect((self.host, self.port)) #Connect to server
        if self.password != None:
            self.s.send("PASS %s\r\n" % self.password)
        self.s.send("NICK %s\r\n" % NICK)
        self.s.send("USER %s %s bla :%s\r\n" % (NICK, self.host, REALNAME))
        self.read()

for server in config.getElementsByTagName('server'):
    srv = Server(server)
    srv.launch()

print ("Nemuspeak ready, waiting for new messages...")
prompt=""
while prompt != "quit":
    prompt=sys.stdin.readlines ()

sys.exit(0)
