# coding=utf-8

import re
import imp
from datetime import datetime
from datetime import timedelta

nemubotversion = 3.0

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "as http://sleepyti.me/, give you the best time to go to bed"

def help_full ():
  return "TODO"


def parseanswer (msg):
  if msg.cmd[0] == "sleepytime" or msg.cmd[0] == "sleeptime":
    if len (msg.cmd) > 1:
      i = int(msg.cmd[1])
      start = datetime.now() + timedelta(minutes=15)
      length = timedelta(hours=1,minutes=30) * i
      msg.send_chn("After %d cycles: %s (during %d:%d)" % (i, start.strftime("%H:%M"), length.seconds/3600, (length.seconds%3600)/60))
    else:
      f = [datetime.now() + timedelta(minutes=15)]
      g = list()
      for i in range(0,6):
        f.append(f[i] + timedelta(hours=1,minutes=30))
        g.append(f[i+1].strftime("%H:%M"))
      msg.send_chn("If you head to bed right now, you should try to wake up at one of the following times: %s"% ', '.join(g))
    return True
  return False
