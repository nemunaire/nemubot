# coding=utf-8

"""as http://sleepyti.me/, give you the best time to go to bed"""

import re
import imp
from datetime import datetime, timedelta, timezone

from hooks import hook

nemubotversion = 3.4

from more import Response

def help_full():
    return "If you would like to sleep soon, use !sleepytime to know the best time to wake up; use !sleepytime hh:mm if you want to wake up at hh:mm"

@hook("cmd_hook", "sleepytime")
def cmd_sleep(msg):
    if len (msg.cmds) > 1 and re.match("[0-9]{1,2}[h':.,-]([0-9]{1,2})?[m'\":.,-]?",
                                      msg.cmds[1]) is not None:
        # First, parse the hour
        p = re.match("([0-9]{1,2})[h':.,-]([0-9]{1,2})?[m':.,-]?", msg.cmds[1])
        f = [datetime(datetime.now(timezone.utc).year,
                      datetime.now(timezone.utc).month,
                      datetime.now(timezone.utc).day,
                      hour=int(p.group(1)))]
        if p.group(2) is not None:
             f[0] += timedelta(minutes=int(p.group(2)))
        g = list()
        for i in range(0,6):
            f.append(f[i] - timedelta(hours=1,minutes=30))
            g.append(f[i+1].strftime("%H:%M"))
        return Response("You should try to fall asleep at one of the following"
                        " times: %s" % ', '.join(g), channel=msg.channel)

    # Just get awake times
    else:
        f = [datetime.now(timezone.utc) + timedelta(minutes=15)]
        g = list()
        for i in range(0,6):
            f.append(f[i] + timedelta(hours=1,minutes=30))
            g.append(f[i+1].strftime("%H:%M"))
        return Response("If you head to bed right now, you should try to wake"
                        " up at one of the following times: %s" %
                        ', '.join(g), channel=msg.channel)
