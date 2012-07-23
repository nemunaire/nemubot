#!/usr/bin/python3
# coding=utf-8

import sys
import socket
import signal
import os
import re
import subprocess
from datetime import datetime
from datetime import timedelta
from xml.dom.minidom import parse
import _thread

if len(sys.argv) <= 1:
    print ("This script takes exactly 1 arg: a XML config file")
    sys.exit(1)

def onSignal(signum, frame):
    print ("\nSIGINT receive, saving states and close")
    sys.exit (0)
signal.signal(signal.SIGINT, onSignal)

if len(sys.argv) == 3:
    basedir = sys.argv[2]
else:
    basedir = "./"

import message

SMILEY = list()
CORRECTIONS = list()
g_queue = list()
talkEC = 0
stopSpk = 0
lastmsg = None

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

for correct in config.getElementsByTagName('correction'):
    if correct.hasAttribute("bad") and correct.hasAttribute("good"):
        CORRECTIONS.append((" " + (correct.getAttribute("bad") + " "), (" " + correct.getAttribute("good") + " ")))
print ("%d corrections loaded"%len(CORRECTIONS))


def speak(endstate):
    global lastmsg, g_queue, talkEC, stopSpk
    talkEC = 1
    stopSpk = 0

    if lastmsg is None:
        lastmsg = message.Message(None, b":Quelqun!someone@p0m.fr PRIVMSG channel nothing")

    while not stopSpk and len(g_queue) > 0:
        msg = g_queue.pop(0)
        lang = "fr"
        sentence = ""
        force = 0

        #Skip identic body
        if msg.content == lastmsg.content:
            continue

        if force or msg.time - lastmsg.time > timedelta(0, 500):
            sentence += "A {0} heure {1} : ".format(msg.time.hour, msg.time.minute)
            force = 1

        if force or msg.channel != lastmsg.channel:
            if msg.channel == OWNER:
                sentence += "En message priver. " #Just to avoid é :p
            else:
                sentence += "Sur " + msg.channel + ". "
            force = 1

        action = 0
        if msg.content.find("ACTION ") == 1:
            sentence += msg.nick + " "
            msg.content = msg.content.replace("ACTION ", "")
            action = 1
        for (txt, mood) in SMILEY:
            if msg.content.find(txt) >= 0:
                sentence += msg.nick + (" %s : "%mood)
                msg.content = msg.content.replace(txt, "")
                action = 1
                break

        for (bad, good) in CORRECTIONS:
            if msg.content.find(bad) >= 0:
                msg.content = (" " + msg.content + " ").replace(bad, good)

        if action == 0 and (force or msg.sender != lastmsg.sender):
            sentence += msg.nick + " dit : "

        if re.match(".*(https?://)?(www\\.)?ycc.fr/[a-z0-9A-Z]+.*", msg.content) is not None:
            msg.content = re.sub("(https?://)?(www\\.)?ycc.fr/[a-z0-9A-Z]+", " U.R.L Y.C.C ", msg.content)

        if re.match(".*https?://.*", msg.content) is not None:
            msg.content = re.sub(r'https?://[^ ]+', " U.R.L ", msg.content)

        if re.match("^ *[^a-zA-Z0-9 ][a-zA-Z]{2}[^a-zA-Z0-9 ]", msg.content) is not None:
            if sentence != "":
                intro = subprocess.call(["espeak", "-v", "fr", sentence])
                #intro.wait()

            lang = msg.content[1:3].lower()
            sentence = msg.content[4:]
        else:
            sentence += msg.content

        spk = subprocess.call(["espeak", "-v", lang, sentence])
        #spk.wait()

        lastmsg = msg

    if not stopSpk:
        talkEC = endstate
    else:
        talkEC = 1


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
        _thread.start_new_thread(self.connect, ())

    def authorize(self, msg):
        return msg.nick != OWNER and (msg.channel == OWNER or msg.channel in self.channels)

    def read(self):
        global stopSpk, talkEC, g_queue
        readbuffer = b"" #Here we store all the messages from server
        while 1:
            raw = self.s.recv(1024) #recieve server messages
            if not raw:
                break
            readbuffer = readbuffer + raw
            temp = readbuffer.split(b"\n")
            readbuffer = temp.pop( )

            for line in temp:
                try:
                    msg = message.Message(self, line)
                except:
                    print ("Une erreur est survenue lors du traitement du message : %s"%line)
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    traceback.print_exception(exc_type, exc_value, exc_traceback)
                    continue

                if msg.cmd == b"PING":
                    self.s.send(("PONG %s\r\n" % msg.content).encode ())
                elif msg.cmd == b"PRIVMSG" and (self.authorize(msg) or msg.content[0] == '`'):
                    if msg.content[0] == '`' and msg.nick == OWNER:
                        cmd = msg.content[1:].split(' ')
                        if cmd[0] == "speak":
                            _thread.start_new_thread(speak, (0,))
                        elif cmd[0] == 'reset':
                            while len(g_queue) > 0:
                                g_queue.pop()
                        elif cmd[0] == 'save':
                            if talkEC == 0:
                                talkEC = 1
                            stopSpk = 1
                        elif cmd[0] == 'test':
                            g_queue.append(message.Message(self, b":Quelqun!someone@p0m.fr PRIVMSG %s :Ceci est un message de test ;)"%(self.channels)))
                        elif cmd[0] == 'list':
                            print ("Currently listened channels:")
                            for chan in self.channels:
                                print (chan)
                            print ("-- ")
                        elif cmd[0] == 'add' and len(cmd) > 1:
                            self.channels.append(cmd[1])
                            print (cmd[1] + " added to listened channels")
                        elif cmd[0] == 'del' and len(cmd) > 1:
                            if self.channels.count(cmd[1]) > 0:
                                self.channels.remove(cmd[1])
                                print (cmd[1] + " removed from listened channels")
                            else:
                                print (cmd[1] + " not in listened channels")

                    else:
                        g_queue.append(msg)
                        if talkEC == 0:
                            _thread.start_new_thread(speak, (0,))

    def connect(self):
        self.s = socket.socket( ) #Create the socket
        self.s.connect((self.host, self.port)) #Connect to server
        if self.password != None:
            self.s.send(("PASS %s\r\n" % self.password).encode())
        self.s.send(("NICK %s\r\n" % NICK).encode())
        self.s.send(("USER %s %s bla :%s\r\n" % (NICK, self.host, REALNAME)).encode())
        self.read()

for server in config.getElementsByTagName('server'):
    srv = Server(server)
    srv.launch()

def sighup_h(signum, frame):
    global talkEC, stopSpk
    sys.stdout.write ("Signal reçu ... ")
    if os.path.exists("/tmp/isPresent"):
        _thread.start_new_thread(speak, (0,))
        print ("Morning!")
    else:
        print ("Sleeping!")
        if talkEC == 0:
            talkEC = 1
        stopSpk = 1
signal.signal(signal.SIGHUP, sighup_h)

print ("Nemuspeak ready, waiting for new messages...")
prompt=""
while prompt != "quit":
    prompt=sys.stdin.readlines ()

sys.exit(0)
