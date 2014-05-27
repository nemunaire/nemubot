#!/usr/bin/python3
# coding=utf-8

import sys
import signal
import os
import re
import subprocess
import traceback
from datetime import datetime
from datetime import timedelta
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

import xmlparser as msf
import message
import IRCServer

SMILEY = list()
CORRECTIONS = list()
g_queue = list()
talkEC = 0
stopSpk = 0
lastmsg = None

def speak(endstate):
    global lastmsg, g_queue, talkEC, stopSpk
    talkEC = 1
    stopSpk = 0

    if lastmsg is None:
        lastmsg = message.Message(b":Quelqun!someone@p0m.fr PRIVMSG channel nothing", datetime.now())

    while not stopSpk and len(g_queue) > 0:
        srv, msg = g_queue.pop(0)
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
            if msg.channel == srv.owner:
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
                intro = subprocess.call(["espeak", "-v", "fr", "--", sentence])
                #intro.wait()

            lang = msg.content[1:3].lower()
            sentence = msg.content[4:]
        else:
            sentence += msg.content

        spk = subprocess.call(["espeak", "-v", lang, "--", sentence])
        #spk.wait()

        lastmsg = msg

    if not stopSpk:
        talkEC = endstate
    else:
        talkEC = 1


class Server(IRCServer.IRCServer):
    def treat_msg(self, line, private = False):
        global stopSpk, talkEC, g_queue
        try:
            msg = message.Message (line, datetime.now(), private)
            if msg.cmd == 'PING':
                self.send_pong(msg.content)
            elif msg.cmd == 'PRIVMSG' and self.accepted_channel(msg.channel):
                if msg.nick != self.owner:
                    g_queue.append((self, msg))
                    if talkEC == 0:
                        _thread.start_new_thread(speak, (0,))
                elif msg.content[0] == "`" and len(msg.content) > 1:
                    msg.cmds = msg.cmds[1:]
                    if msg.cmds[0] == "speak":
                        _thread.start_new_thread(speak, (0,))
                    elif msg.cmds[0] == "reset":
                        while len(g_queue) > 0:
                            g_queue.pop()
                    elif msg.cmds[0] == "save":
                        if talkEC == 0:
                            talkEC = 1
                        stopSpk = 1
                    elif msg.cmds[0] == "add":
                        self.channels.append(msg.cmds[1])
                        print (cmd[1] + " added to listened channels")
                    elif msg.cmds[0] == "del":
                        if self.channels.count(msg.cmds[1]) > 0:
                            self.channels.remove(msg.cmds[1])
                            print (msg.cmds[1] + " removed from listened channels")
                        else:
                            print (cmd[1] + " not in listened channels")
        except:
            print ("\033[1;31mERROR:\033[0m occurred during the processing of the message: %s" % line)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)


config = msf.parse_file(sys.argv[1])

for smiley in config.getNodes("smiley"):
    if smiley.hasAttribute("txt") and smiley.hasAttribute("mood"):
        SMILEY.append((smiley.getAttribute("txt"), smiley.getAttribute("mood")))
print ("%d smileys loaded"%len(SMILEY))

for correct in config.getNodes("correction"):
    if correct.hasAttribute("bad") and correct.hasAttribute("good"):
        CORRECTIONS.append((" " + (correct.getAttribute("bad") + " "), (" " + correct.getAttribute("good") + " ")))
print ("%d corrections loaded"%len(CORRECTIONS))

for serveur in config.getNodes("server"):
    srv = Server(serveur, config["nick"], config["owner"], config["realname"], serveur.hasAttribute("ssl"))
    srv.launch(None)

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
