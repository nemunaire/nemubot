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

imports = ["birthday", "qd", "events", "youtube", "watchWebsite", "soutenance", "whereis", "alias"]
imports_launch = ["watchWebsite", "events"]
mods = {}
import server, message

if len(sys.argv) != 2 and len(sys.argv) != 3:
    print ("This script takes exactly 1 arg: a XML config file")
    sys.exit(1)


def onSignal(signum, frame):
    print ("\nSIGINT receive, saving states and close")

    for imp in mods.keys():
        mods[imp].save_module ()

    for imp in imports_launch:
        mods[imp].stop ()

    #Save banlist before quit
    message.save_module ()

    sys.exit (0)
signal.signal(signal.SIGINT, onSignal)

if len(sys.argv) == 3:
    basedir = sys.argv[2]
else:
    basedir = "./"

dom = parse(sys.argv[1])
config = dom.getElementsByTagName('config')[0]
servers = dict ()

message.load_module (basedir + "/datas/")

for imp in imports:
    mod = __import__ (imp)
    mods[imp] = mod
    mod.load_module (basedir + "/datas/")

for serveur in config.getElementsByTagName('server'):
    srv = server.Server(serveur, config.getAttribute('nick'), config.getAttribute('owner'), config.getAttribute('realname'))
    srv.launch(mods, basedir + "/datas/")
    servers[srv.id] = srv

for imp in imports_launch:
    mod = __import__ (imp)
    mod.launch (servers)

print ("Nemubot ready, my PID is %i!" % (os.getpid()))
prompt=""
while prompt != "quit":
    prompt=sys.stdin.readlines ()

sys.exit(0)
