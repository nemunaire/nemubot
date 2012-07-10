#!/usr/bin/python3
# coding=utf-8

import sys
import os
import imp
import traceback

servers = dict()

prompt = __import__ ("prompt")

#Add modules dir path
if os.path.isdir("./modules/"):
  modules_path = os.path.realpath(os.path.abspath("./modules/"))
  if modules_path not in sys.path:
        sys.path.insert(0, modules_path)

#Load given files
if len(sys.argv) >= 2:
    for arg in sys.argv[1:]:
        if os.path.isfile(arg):
            prompt.load_file(arg, servers)
        elif os.path.isdir(arg):
            sys.path.insert(1, arg)

print ("Nemubot ready, my PID is %i!" % (os.getpid()))
while prompt.launch(servers):
    try:
      if prompt.MODS is None:
        imp.reload(prompt)
      else:
        mods = prompt.MODS
        imp.reload(prompt)
        prompt.MODS = mods
    except:
        print ("Unable to reload the prompt due to errors. Fix them before trying to reload the prompt.")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sys.stdout.write (traceback.format_exception_only(exc_type, exc_value)[0])

print ("Bye")
sys.exit(0)
