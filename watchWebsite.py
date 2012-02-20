# coding=utf-8
import httplib
import hashlib
import time

def getPage(s, p):
    conn = httplib.HTTPConnection(s)
    conn.request("GET", "/%s"%(p))

    res = conn.getresponse()
    data = res.read()

    conn.close()
    return data

def startThread(s, a, p, CHANLIST, message):
    lastpage = hashlib.sha224(getPage(a, p)).hexdigest()
    time.sleep(2)
    while 1:
        page = hashlib.sha224(getPage(a, p)).hexdigest()

        if page != lastpage:
            print("Page differ!")
            for chan in CHANLIST.split():
                s.send("PRIVMSG %s :%s\r\n" % (chan, message))
            lastpage = page

        time.sleep(60)
