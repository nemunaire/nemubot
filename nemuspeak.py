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
import thread

if len(sys.argv) < 3:
    print "This script takes at least 2 args: server port [channel [channel [...]]]"
    sys.exit(0)

#HOST='192.168.0.242'
#HOST = 'nemunai.re'
#PORT = 2778
HOST = sys.argv[1]
PORT = int(sys.argv[2])
#HOST = 'irc.rezosup.org'
#PORT = 6667
NICK = 'nemunaire'
IDENT = 'nemuspeak'
REALNAME = 'nemubot speaker'
OWNER = 'nemunaire' #The bot owner's nick
#CHANLIST = ['#42sh', '#korteam']
CHANLIST = []
if len(sys.argv) > 3:
    for i in range(3, len(sys.argv)):
        CHANLIST.append(sys.argv[i])
readbuffer = '' #Here we store all the messages from server

queue = []
talkEC = 0
stopSpk = 0
lastmsg = []

s = socket.socket( ) #Create the socket
s.connect((HOST, PORT)) #Connect to server
s.send("PASS %s\r\n" % "McsuapTesbuf")
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
#s.send("JOIN %s\r\n" % CHANLIST)

print("Welcome on Nemubot speaker. I operate on %s. My PID is %i" % (CHANLIST, os.getpid()))

def speak(endstate):
    global lastmsg, queue, talkEC, stopSpk
    talkEC = 1
    stopSpk = 0

    if len(lastmsg) < 1:
        lastmsg = queue.pop(0)

    while not stopSpk and len(queue) > 0:
        msg = queue.pop(0)
        lang = "fr"

        sentence = ""
        force = 0

        if force or msg[2] - lastmsg[2] > timedelta(0, 500):
            sentence += "À {0} heure {1} : ".format(msg[2].hour, msg[2].minute)
            force = 1

        if force or msg[0] != lastmsg[0]:
            if msg[0] == NICK:
                sentence += "En message privé. "
            else:
                sentence += "Sur " + msg[0] + ". "
            force = 1

        if msg[3].find("ACTION ") == 1:
            sentence += msg[1] + " "
            msg[3] = msg[3].replace("ACTION ", "")
        elif msg[3].find(":)") >= 0:
            sentence += msg[1] + " sourit : "
            msg[3] = msg[3].replace(":)", "")
        elif msg[3].find(";)") >= 0:
            sentence += msg[1] + " fait un clin d'oeil : "
            msg[3] = msg[3].replace(";)", "")
        elif msg[3].find(":(") >= 0:
            sentence += msg[1] + " est triste : "
            msg[3] = msg[3].replace(":(", "")
        elif msg[3].find("<3") >= 0:
            sentence += msg[1] + " aime : "
            msg[3] = msg[3].replace("<3", "")
        elif msg[3].find(":'(") >= 0 or msg[3].find(";(") >= 0:
            sentence += msg[1] + " pleure : "
            msg[3] = msg[3].replace(":'(", "")
            msg[3] = msg[3].replace(";(", "")
        elif msg[3].find(":D") >= 0 or msg[3].find(":d") >= 0:
            sentence += msg[1] + " rit : "
            msg[3] = msg[3].replace(":D", "")
            msg[3] = msg[3].replace(":d", "")
        elif msg[3].find(":P") >= 0 or msg[3].find(":p") >= 0:
            sentence += msg[1] + " tire la langue : "
            msg[3] = msg[3].replace(":P", "")
            msg[3] = msg[3].replace(":p", "")
        elif msg[3].find(":S") >= 0 or msg[3].find(":s") >= 0:
            sentence += msg[1] + " est embarassé : "
            msg[3] = msg[3].replace(":S", "")
            msg[3] = msg[3].replace(":s", "")
        elif msg[3].find("XD") >= 0 or msg[3].find("xd") >= 0 or msg[3].find("xD") >= 0 or msg[3].find("Xd") >= 0 or msg[3].find("X)") >= 0 or msg[3].find("x)") >= 0:
            sentence += msg[1] + " se marre : "
            msg[3] = msg[3].replace("xd", "")
            msg[3] = msg[3].replace("XD", "")
            msg[3] = msg[3].replace("Xd", "")
            msg[3] = msg[3].replace("xD", "")
            msg[3] = msg[3].replace("X)", "")
            msg[3] = msg[3].replace("x)", "")
        elif msg[3].find("\\o/") >= 0 or msg[3].find("\\O/") >= 0:
            sentence += msg[1] + " fait une accolade : "
            msg[3] = msg[3].replace("\\o/", "")
            msg[3] = msg[3].replace("\\O/", "")
        elif msg[3].find("/o/") >= 0 or msg[3].find("\\o\\") >= 0:
            sentence += msg[1] + " danse : "
            msg[3] = msg[3].replace("/o/", "")
            msg[3] = msg[3].replace("\\o\\", "")

        elif force or msg[1] != lastmsg[1]:
            sentence += msg[1] + " dit : "

        if re.match(".*(https?://)?(www\\.)?ycc.fr/[a-z0-9A-Z]+.*", msg[3]) is not None:
            msg[3] = re.sub("(https?://)?(www\\.)?ycc.fr/[a-z0-9A-Z]+", " U.R.L Y.C.C ", msg[3])

        if re.match(".*https?://.*", msg[3]) is not None:
            msg[3] = re.sub(r'https?://[^ ]+', " U.R.L ", msg[3])

        if re.match("^ *[^a-zA-Z0-9 ][a-zA-Z]{2}[^a-zA-Z0-9 ]", msg[3]) is not None:
            if sentence != "":
                subprocess.call(["espeak", "-v", "fr", sentence])

            lang = msg[3][1:3].lower()
            sentence = msg[3][4:]
        else:
            sentence += msg[3]

        subprocess.call(["espeak", "-v", lang, sentence])

        lastmsg = msg

    if not stopSpk:
        talkEC = endstate
    else:
        talkEC = 1


def parsemsg(msg):
    global talkEC, stopSpk, queue
    complete = msg[1:].split(':',1) #Parse the message into useful data
    info = complete[0].split(' ')
    msgpart = complete[1]
    sender = info[0].split('!')

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
                while len(queue) > 0:
                    queue.pop()

            elif cmd[0] == 'save':
                if talkEC == 0:
                    talkEC = 1
                stopSpk = 1

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

        elif sender[0] != OWNER and (len(CHANLIST) == 0 or CHANLIST.count(info[2]) > 0 or info[2] == NICK):
            queue.append([info[2], sender[0], datetime.now(), msgpart])
            if talkEC == 0:
                thread.start_new_thread(speak, (0,))


def read():
    global s, readbuffer
    while 1:
        readbuffer = readbuffer + s.recv(1024) #recieve server messages
        temp = readbuffer.split("\n")
        readbuffer = temp.pop( )

        for line in temp:
            line = line.rstrip() #remove trailing 'rn'

            if line.find('PRIVMSG') != -1: #Call a parsing function
                parsemsg(line)

            line = line.split()

            if(line[0] == 'PING'): #If server pings then pong
                s.send("PONG %s\r\n" % line[1])

read()
