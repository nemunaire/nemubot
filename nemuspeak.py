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

if len(sys.argv) > 1:
    sys.exit(0)

#HOST='192.168.0.242'
HOST = 'nemunai.re'
PORT = 2778
#HOST = 'irc.rezosup.org'
#PORT = 6667
NICK = 'nemunaire'
IDENT = 'nemuspeak'
REALNAME = 'nemubot speaker'
OWNER = 'nemunaire' #The bot owner's nick
CHANLIST = ['#42sh', '#korteam']
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
    global lastmsg
    talkEC = 1
    stopSpk = 0

    if len(lastmsg) < 1:
        lastmsg = queue.pop(0)

    while not stopSpk and len(queue) > 0:
        msg = queue.pop(0)

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

        if force or msg[1] != lastmsg[1]:
            sentence += msg[1] + " dit : "

        sentence += msg[3]

        print "Blabla: " + sentence
        subprocess.call(["espeak", "-v", "fr", sentence])

        lastmsg = msg

    talkEC = endstate


def parsemsg(msg):
    complete = msg[1:].split(':',1) #Parse the message into useful data
    info = complete[0].split(' ')
    msgpart = complete[1]
    sender = info[0].split('!')

    if CHANLIST.count(info[2]) >= 0 or info[2] == NICK:
        #Treat all messages starting with '`' as command
        if msgpart[0] == '`' and sender[0] == OWNER:
            cmd=msgpart[1:].split(' ')

            if cmd[0] == 'stop':
                print "Bye!"
                sys.exit (0)

            elif cmd[0] == 'speak':
                thread.start_new_thread(speak, (0,))

            elif cmd[0] == 'save':
                stopSpk = 1

            elif cmd[0] == 'add' and len(cmd) > 1:
                CHANLIST.append(cmd[1])
                print cmd[1] + " added to listed channels"


        elif sender[0] != OWNER:
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
