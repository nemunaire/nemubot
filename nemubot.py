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

imports = ["birthday", "qd", "events", "youtube", "watchWebsite", "soutenance", "whereis"]
imports_launch = ["watchWebsite"]
mods = {}
import server

if len(sys.argv) != 2 and len(sys.argv) != 3:
    print ("This script takes exactly 1 arg: a XML config file")
    sys.exit(1)


def onSignal(signum, frame):
    print ("\nSIGINT receive, saving states and close")

    for imp in mods.keys():
        mods[imp].save_module ()

    sys.exit (0)
signal.signal(signal.SIGINT, onSignal)

if len(sys.argv) == 3:
    basedir = sys.argv[2]
else:
    basedir = "./"
print (basedir, len(sys.argv))

dom = parse(sys.argv[1])
config = dom.getElementsByTagName('config')[0]
servers = list ()

for imp in imports:
    mod = __import__ (imp)
    mods[imp] = mod
    mod.load_module (basedir + "/datas/")

for serveur in config.getElementsByTagName('server'):
    srv = server.Server(serveur, config.getAttribute('nick'), config.getAttribute('owner'), config.getAttribute('realname'))
    srv.launch(mods, basedir + "/datas/")
    servers.append (srv)

for imp in imports_launch:
    mod = __import__ (imp)
    mod.launch (servers)

print ("Nemubot ready, my PID is %i!" % (os.getpid()))
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
            print ("Restarting thread")
            launch(s)
        if cmd[0]=='stop':
            print ("Bye!")
            s.send("PRIVMSG %s :Bye!\r\n"%(info[2]))
            sys.exit (0)
        if cmd[0]=='sys':
            syscmd(msgpart[1:],info[2])

    if msgpart[0]=='-' and sender[0]==OWNER : #Treat msgs with - as explicit command to send to server
        cmd=msgpart[1:]
        #s.send(cmd+'n')
        print ('cmd='+cmd)

def read():
    global s, readbuffer
    while 1:
        readbuffer = readbuffer + s.recv(1024) #recieve server messages
        temp = readbuffer.split("\n")
        readbuffer = temp.pop( )
        #signal.signal(signal.SIGHUP, onSignal)

        for line in temp:
            print (line)
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
    print ("Launched successfuly")

launch(s)
read()
