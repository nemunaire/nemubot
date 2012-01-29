# coding=utf-8
import httplib
import hashlib
import time

def getPage(s, p):
    conn = httplib.HTTPConnection(s)
    conn.request("GET", "/{0}".format(p))

    res = conn.getresponse()
    data = res.read()

    conn.close()
    return data

def startThread(s, a, p, CHANLIST):
    lastpage = hashlib.sha224(getPage(a, p)).hexdigest()
    time.sleep(2)
    while 1:
        page = hashlib.sha224(getPage(a, p)).hexdigest()

        if page != lastpage:
            print("Page differ!")
            for chan in CHANLIST.split():
                s.send("PRIVMSG %s :Oh, quelle est cette nouvelle image sur http://you.p0m.fr/ ? :p\r\n" % chan)
            lastpage = page

        time.sleep(60)
