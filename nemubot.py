#!/usr/bin/python3
# coding=utf-8

import sys
import signal
import os
import re
import imp
from datetime import date
from datetime import datetime
from datetime import timedelta
from xml.dom.minidom import parse

if len(sys.argv) != 2 and len(sys.argv) != 3:
    print ("This script takes exactly 1 arg: a XML config file")
    sys.exit(1)

imports = ["birthday", "qd", "events", "youtube", "watchWebsite", "soutenance", "whereis", "alias"]
imports_launch = ["watchWebsite", "events"]
mods = {}

def onClose():
    """Call when the bot quit; saving all modules"""
    for imp in mods.keys():
        mods[imp].save_module ()

    for imp in imports_launch:
        mods[imp].stop ()

    #Save banlist before quit
    message.save_module ()

    sys.exit (0)

def onSignal(signum, frame):
    print ("\nSIGINT receive, saving states and close")
    onClose()
signal.signal(signal.SIGINT, onSignal)

#Define working directory
if len(sys.argv) == 3:
    basedir = sys.argv[2]
else:
    basedir = "./"

#Load base modules
server = __import__ ("server")
message = __import__ ("message")
message.load (basedir + "/datas/")

#Read configuration XML file
dom = parse(sys.argv[1])
config = dom.getElementsByTagName('config')[0]
servers = dict ()

#Load modules
for imp in imports:
    mod = __import__ (imp)
    mods[imp] = mod

for serveur in config.getElementsByTagName('server'):
    srv = server.Server(serveur, config.getAttribute('nick'), config.getAttribute('owner'), config.getAttribute('realname'))
    srv.launch(mods, basedir + "/datas/")
    servers[srv.id] = srv


print ("Nemubot ready, my PID is %i!" % (os.getpid()))

prompt = __import__ ("prompt")
while prompt.launch(servers):
    imp.reload(prompt)

onClose()
