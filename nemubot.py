#!/usr/bin/python3
# coding=utf-8

import sys
import os
import imp
import traceback

servers = dict()

print ("Nemubot ready, my PID is %i!" % (os.getpid()))
prompt = __import__ ("prompt")
while prompt.launch(servers):
    try:
        imp.reload(prompt)
    except:
        print ("Unable to reload the prompt due to errors. Fix them before trying to reload the prompt.")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sys.stdout.write (traceback.format_exception_only(exc_type, exc_value)[0])

print ("Bye")
sys.exit(0)
