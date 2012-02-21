#!/usr/bin/python2.7
# coding=utf-8

import sys
import socket
import string
import os
import re
import thread
from datetime import date
from datetime import datetime
from datetime import timedelta
from xml.dom.minidom import parse

import birthday
import norme
import newyear
import ontime
import watchWebsite
import qd

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

def parsemsg(msg):
    global birthdays, score42
    complete = msg[1:].split(':',1) #Parse the message into useful data
    info = complete[0].split(' ')
    msgpart = complete[1]
    sender = info[0].split('!')

    if len(msgpart) <= 0:
        return

    qd.go (s, sender, msgpart, info[2])

    if CHANLIST.find(info[2]) != -1 and re.match(".*(norme|coding style).*", msgpart) is not None and re.match(".*(please|give|obtenir|now|plz|stp|svp|s'il (te|vous) pla.t|check).*", msgpart) is not None:
        norme.launch (s, sender, msgpart)

    elif CHANLIST.find(info[2]) != -1 and msgpart[0] == '!': #Treat all messages starting with '!' as command
        cmd = msgpart[1:].split(' ')
        if cmd[0] == 'help' or cmd[0] == 'h':
            s.send("PRIVMSG %s :Pour me demander quelque chose, commencer votre message par !.\nVoici ce dont je suis capable :\r\n"%(sender[0]))
            s.send("PRIVMSG %s :  - !new-year !newyear !ny : Affiche le temps restant avant la nouvelle année\r\n"%(sender[0]))
            s.send("PRIVMSG %s :  - !end-of-world !worldend !eow : Temps restant avant la fin du monde\r\n"%(sender[0]))
            s.send("PRIVMSG %s :  - !weekend !week-end !we : Affiche le temps restant avant le prochain week-end\r\n"%(sender[0]))
            s.send("PRIVMSG %s :  - !partiels : Affiche le temps restant avant les prochains partiels\r\n"%(sender[0]))
            s.send("PRIVMSG %s :  - !vacs !vacances !holidays !free-time : Affiche le temps restant avant les prochaines vacances\r\n"%(sender[0]))
            s.send("PRIVMSG %s :  - !jpo !next-jpo : Affiche le temps restant avant la prochaine JPO\r\n"%(sender[0]))
            s.send("PRIVMSG %s :  - !42 !scores : Affiche les scores des gens\r\n"%(sender[0]))

        if cmd[0] == 'score' or cmd[0] == 'scores' or cmd[0] == '42':
            qd.scores(s, cmd, info[2])

        if cmd[0] == 'chronos' or cmd[0] == 'edt' or cmd[0] == 'cours':
            s.send("PRIVMSG %s :chronos\r\n"%(info[2]))

        if cmd[0] == 'new-year' or cmd[0] == 'newyear' or cmd[0] == 'ny':
            #What is the next year?
            nyear = datetime.today().year + 1
            ndate = datetime(nyear, 1, 1, 0, 0, 1)
            newyear.launch (s, info[2], ndate, ["Il reste%s avant la nouvelle année", "Nous faisons déjà la fête depuis%s"], cmd)
        if cmd[0] == 'end-of-world' or cmd[0] == 'endofworld' or cmd[0] == 'worldend' or cmd[0] == 'eow':
            ndate = datetime(2012, 12, 12, 12, 12, 13)
            newyear.launch (s, info[2], ndate, ["Il reste%s avant la fin du monde", "Non, cela ne peut pas arriver, la fin du monde s'est produite il y a maintenant %s. Vous n'êtes vraiment pas mort ? :("], cmd)
        if cmd[0] == 'weekend' or cmd[0] == 'week-end' or cmd[0] == 'we':
            ndate = datetime.today() + timedelta(5 - datetime.today().weekday())
            ndate = datetime(ndate.year, ndate.month, ndate.day, 0, 0, 1)
            newyear.launch (s, info[2], ndate, ["Il reste%s avant le week-end, courrage ;)", "Youhou, on est en week-end depuis%s"], cmd)
        if cmd[0] == 'google' or cmd[0] == 'eog':
            ndate = datetime(2012, 3, 1, 0, 0, 1)
            newyear.launch (s, info[2], ndate, ["Il reste%s pour fermer tous ces comptes Google, hop hop hop, il y a du boulot !", "Nous ne pouvons plus utiliser les services de Google depuis%s"], cmd)
        if cmd[0] == 'endweekend' or cmd[0] == 'end-week-end' or cmd[0] == 'endwe' or cmd[0] == 'eowe':
            ndate = datetime.today() + timedelta(7 - datetime.today().weekday())
            ndate = datetime(ndate.year, ndate.month, ndate.day, 0, 0, 1)
            if datetime.today().weekday() >= 5:
                newyear.launch (s, info[2], ndate, ["Plus que%s avant la fin du week-end :(", ""], cmd)
            else:
                newyear.launch (s, info[2], ndate, ["Encore%s avant la prochaine semaine", ""], cmd)
        if cmd[0] == 'partiels' or cmd[0] == 'partiel':
            ndate = datetime(2012, 3, 26, 9, 0, 1)
            #ndate = datetime(2012, 1, 23, 9, 0, 1)
            newyear.launch (s, info[2], ndate, ["Il reste%s avant les partiels :-o", "Les partiels ont commencés depuis maintenant%s"], cmd)
        if cmd[0] == 'vacs' or cmd[0] == 'vacances' or cmd[0] == 'holiday' or cmd[0] == 'holidays' or cmd[0] == 'free-time':
            ndate = datetime(2012, 3, 30, 18, 0, 1)
            newyear.launch (s, info[2], ndate, ["Il reste%s avant les vacances :)", "Profitons, c'est les vacances depuis%s"], cmd)
        if cmd[0] == 'katy' or cmd[0] == 'album':
            ndate = datetime(2012, 3, 26, 8, 0, 0)
            newyear.launch (s, info[2], ndate, ["Il reste%s avant la sortie du prochain album de Katy Perry :)", "Vite, courrons s'acheter le nouvel album de Katy Perry, il est sorti depuis%s"], cmd)
        if cmd[0] == 'anniv' or cmd[0] == 'age':
            if len(cmd) < 2 or cmd[1].lower() == "moi":
                name = sender[0].lower()
            else:
                name = cmd[1].lower()

            matches = []

            if name in birthdays:
                matches.append(name)
            else:
                for k in birthdays.keys():
                    if k.find(name) == 0:
                        matches.append(k)

            if len(matches) == 1:
                (n, d) = (matches[0], birthdays[matches[0]])
                tyd = d
                tyd = datetime(date.today().year, tyd.month, tyd.day)

                if tyd.day == datetime.today().day and tyd.month == datetime.today().month:
                    newyear.launch (s, info[2], d, ["", "C'est aujourd'hui l'anniversaire de %s ! Il a%s. Joyeux anniversaire :)" % (n, "%s")], cmd)
                else:
                    if tyd < datetime.today():
                        tyd = datetime(date.today().year + 1, tyd.month, tyd.day)

                    if cmd[0] == 'age':
                        newyear.launch (s, info[2], d, ["", "%s a%s aujourd'hui !" % (n, "%s")], cmd)
                    else:
                        newyear.launch (s, info[2], tyd, ["Il reste%s avant l'anniversaire de %s !" % ("%s", n), ""], cmd)
            else:
                s.send("PRIVMSG %s :%s: désolé, je ne connais pas la date d'anniversaire de %s. Quand est-il né ?\r\n"%(info[2], sender[0], name))

        if cmd[0] == 'jpo' or cmd[0] == 'JPO' or cmd[0] == 'next-jpo':
            #ndate = datetime(2012, 5, 12, 8, 30, 1)
            #ndate = datetime(2012, 3, 31, 8, 30, 1)
            ndate = datetime(2012, 3, 17, 8, 30, 1)
            #ndate = datetime(2012, 2, 4, 8, 30, 1)
            newyear.launch (s, info[2], ndate, ["Il reste%s avant la prochaine JPO... We want you!", "Nous somme en pleine JPO depuis%s"], cmd)
        if cmd[0] == 'professional-project' or cmd[0] == 'project-professionnel' or cmd[0] == 'projet-professionnel' or cmd[0] == 'project-professionel' or cmd[0] == 'tc' or cmd[0] == 'next-rendu' or cmd[0] == 'rendu':
            ndate = datetime(2012, 3, 18, 23, 42, 1)
            newyear.launch (s, info[2], ndate, ["Il reste%s avant la fermeture du rendu de TC-5 et de corewar, vite au boulot !", "À %s près, il aurait encore été possible de rendre"], cmd)


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
            launch(s)
        if cmd[0]=='stop':
            print "Bye!"
            s.send("PRIVMSG %s :Bye!\r\n"%(info[2]))
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
            line = line.rstrip() #remove trailing 'rn'

            if line.find('PRIVMSG') != -1: #Call a parsing function
                parsemsg(line)

            line = line.split()

            if(line[0] == 'PING'): #If server pings then pong
                s.send("PONG %s\r\n" % line[1])

def launch(s):
#    thread.start_new_thread(ontime.startThread, (s,datetime(2012, 1, 18, 6, 0, 1),["Il reste%s avant la fin de Wikipédia", "C'est fini, Wikipédia a sombrée depuis%s"],CHANLIST))
#    thread.start_new_thread(ontime.startThread, (s,datetime(2012, 2, 23, 0, 0, 1),[],CHANLIST))
    thread.start_new_thread(watchWebsite.startThread, (s, "you.p0m.fr", "", "#42sh #epitaguele", "Oh, quelle est cette nouvelle image sur http://you.p0m.fr/ ? :p"))
    thread.start_new_thread(watchWebsite.startThread, (s, "intra.nbr23.com", "", "#42sh", "Oh, quel est ce nouveau film sur http://intra.nbr23.com/ ? :p"))
    print "Launched successfuly"

launch(s)
read()
