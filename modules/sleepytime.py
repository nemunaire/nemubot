# coding=utf-8

import re
import imp
from datetime import datetime
from datetime import timedelta

nemubotversion = 3.2

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "as http://sleepyti.me/, give you the best time to go to bed"

def help_full ():
  return "TODO"

def load(context):
    from hooks import Hook
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(cmd_sleep, "sleeptime"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(cmd_sleep, "sleepytime"))


def cmd_sleep(msg):
    if len (msg.cmd) > 1 and re.match("[0-9]{1,2}[h':.,-]([0-9]{1,2})?[m'\":.,-]?",
                                      msg.cmd[1]) is not None:
        # First, parse the hour
        p = re.match("([0-9]{1,2})[h':.,-]([0-9]{1,2})?[m':.,-]?", msg.cmd[1])
        f = [datetime(datetime.today().year,
                      datetime.today().month,
                      datetime.today().day,
                      hour=int(p.group(1)))]
        if p.group(2) is not None:
             f[0] += timedelta(minutes=int(p.group(2)))
        g = list()
        for i in range(0,6):
            f.append(f[i] - timedelta(hours=1,minutes=30))
            g.append(f[i+1].strftime("%H:%M"))
        return Response(msg.sender,
                        "You should try to fall asleep at one of the following"
                        " times: %s" % ', '.join(g), msg.channel)

    # Just get awake times
    else:
        f = [datetime.now() + timedelta(minutes=15)]
        g = list()
        for i in range(0,6):
            f.append(f[i] + timedelta(hours=1,minutes=30))
            g.append(f[i+1].strftime("%H:%M"))
        return Response(msg.sender,
                        "If you head to bed right now, you should try to wake"
                        " up at one of the following times: %s" %
                        ', '.join(g), msg.channel)
