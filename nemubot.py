#!/usr/bin/python2.7
# coding=utf-8

#import signal
import sys
import socket
import string
import os
import re
import thread

import norme
import newyear
import ontime

if len(sys.argv) > 1:
    sys.exit(0)

HOST='192.168.0.242'
PORT=2770
#HOST='irc.rezosup.org'
#PORT=6667
NICK='nemubot'
IDENT='nemubot'
REALNAME='nemubot'
OWNER='nemunaire' #The bot owner's nick
#CHANLIST='#nemutest'
CHANLIST='#42sh #nemutest'
readbuffer='' #Here we store all the messages from server

s = socket.socket( ) #Create the socket
s.connect((HOST, PORT)) #Connect to server
s.send("PASS %s\r\n" % "McsuapTesbuf")
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
#s.send("JOIN %s\r\n" % CHANLIST)

print("Welcome on Nemubot. I operate on %s. My PID is %i" % (CHANLIST, os.getpid()))

def parsemsg(msg):
    complete = msg[1:].split(':',1) #Parse the message into useful data
    info = complete[0].split(' ')
    msgpart = complete[1]
    sender = info[0].split('!')

    if CHANLIST.find(info[2]) != -1 and re.match(".*(norme|coding style).*", msgpart) is not None and re.match(".*(please|give|obtenir|now|plz|stp|svp|s'il (te|vous) pla.t|check).*", msgpart) is not None:
        norme.launch (s, sender, msgpart)

    elif msgpart[0] == '!' and CHANLIST.find(info[2]) != -1: #Treat all messages starting with '!' as command
        cmd=msgpart[1:].split(' ')
        if cmd[0] == 'new-year' or cmd[0] == 'newyear' or cmd[0] == 'ny':
            newyear.launch (s, info[2], cmd)


    elif msgpart[0] == '`' and sender[0] == OWNER and CHANLIST.find(info[2]) != -1: #Treat all messages starting with '`' as command
        cmd=msgpart[1:].split(' ')
        if cmd[0]=='op':
            s.send("MODE %s +o %s\r\n" % (info[2], cmd[1]))
        if cmd[0]=='deop':
            s.send("MODE %s -o %s\r\n" % (info[2], cmd[1]))
        if cmd[0]=='voice':
            s.send('MODE '+info[2]+' +v '+cmd[1]+'n')
        if cmd[0]=='devoice':
            s.send('MODE '+info[2]+' -v '+cmd[1]+'n')
        if cmd[0]=='restart':
            print "Restarting thread"
            thread.start_new_thread(ontime.startThread, (s,CHANLIST))
        if cmd[0]=='stop':
            print "Bye!"
            s.send("PRIVMSG {0} :Bye!\r\n".format(info[2]))
            sys.exit (0)
        if cmd[0]=='sys':
            syscmd(msgpart[1:],info[2])

    if msgpart[0]=='-' and sender[0]==OWNER : #Treat msgs with - as explicit command to send to server
        cmd=msgpart[1:]
        #s.send(cmd+'n')
        print 'cmd='+cmd

def read():
    global s, readbuffer
    while 1:
        readbuffer = readbuffer + s.recv(1024) #recieve server messages
        temp = readbuffer.split("\n")
        readbuffer = temp.pop( )
        #signal.signal(signal.SIGHUP, onSignal)

        for line in temp:
            print line
            line = line.rstrip() #remove trailing 'rn'

            if line.find('PRIVMSG') != -1: #Call a parsing function
                parsemsg(line)

            line = line.split()

            if(line[0] == 'PING'): #If server pings then pong
                s.send("PONG %s\r\n" % line[1])

thread.start_new_thread(ontime.startThread, (s,CHANLIST))
read()
