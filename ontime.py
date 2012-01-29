# coding=utf-8
from datetime import datetime
import time

import newyear

def sync(sec):
    print "Time thread synchronization..."

    time.sleep(((60 + sec) - datetime.now().second - 1) % 60)

    while datetime.now().second % sec != 0:
        time.sleep (0.1)

    time.sleep (0.4)

    print "Synchonized on {0}={1} seconds...".format(sec, datetime.now().second)


def startThread(s, ndate, sentences, CHANLIST):
    sync (60);
    while 1:
        minute = datetime.now ().minute

        if minute == 0 and datetime.now ().hour == 0 and datetime.now ().day == 1 and datetime.now ().month == 1:
            print("Happy new year!")
            for chan in CHANLIST.split():
                newyear.special (s, chan)

        elif minute == 0 and datetime.now ().hour == 6 and datetime.now ().day == 18 and datetime.now ().month == 1:
            print("WikiEnd!")
            for chan in CHANLIST.split():
                newyear.special (s, chan)

        if minute == 18:
            for chan in CHANLIST.split():
                newyear.launch (s, chan, datetime(2012, 1, 18, 6, 0, 1), sentences, 0)

        if minute == 42:
            sync(42)
            print("42!")
#            for chan in CHANLIST.split():
#                s.send("PRIVMSG %s :42 !\r\n" % chan)

        if datetime.now ().second != 0:
            sync(60)
        else:
            time.sleep(60)
