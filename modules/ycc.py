# coding=utf-8

import http.client
import imp
import re
import sys

nemubotversion = 3.3

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Gets YCC urls"

def help_full ():
  return "!ycc [<url>]: with an argument, reduce the given <url> thanks to ycc.fr; without argument, reduce the last URL said on the current channel."

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_ycc, "ycc"))
    add_hook("all_post", Hook(parseresponse))

LAST_URLS = dict()

def gen_response(res, msg, srv):
    if res is None:
        return Response(msg.sender, "La situation est embarassante, il semblerait que YCC soit down :(", msg.channel)
    elif isinstance(res, str):
        return Response(msg.sender, "URL pour %s : %s" % (srv, res), msg.channel)
    else:
        return Response(msg.sender, "Mauvaise URL : %s" % srv, msg.channel)

def cmd_ycc(msg):
    if len(msg.cmds) == 1:
        global LAST_URLS
        if msg.channel in LAST_URLS and len(LAST_URLS[msg.channel]) > 0:
            msg.cmds.append(LAST_URLS[msg.channel].pop())
        else:
            return Response(msg.sender, "Je n'ai pas d'autre URL à réduire.", msg.channel)

    if len(msg.cmds) < 6:
        res = list()
        for url in msg.cmds[1:]:
            srv = re.match(".*((ht|f)tps?://|www.)([^/ ]+).*", url)
            if srv is not None:
                res.append(gen_response(tinyfy(url), msg, srv.group(3)))
            else:
                res.append(gen_response(False, msg, url))
        return res
    else:
        return Response(msg.sender, "je ne peux pas réduire autant d'URL "
                     "d'un seul coup.", msg.channel, nick=msg.nick)

def parselisten(msg):
    global LAST_URLS
    res = re.match(".*(((ht|f)tps?://|www\.)[^ ]+).*", msg.content)
    if res is not None:
        if res.group(1).find("ycc.fr") >= 0:
            return False
        if msg.channel not in LAST_URLS:
            LAST_URLS[msg.channel] = list()
        LAST_URLS[msg.channel].append(res.group(1))
        return True
    return False
def parseresponse(res):
    parselisten(res)
    return True

def tinyfy(url):
    (status, page) = getPage("ycc.fr", "/redirection/create/" + url)
    if status == http.client.OK and len(page) < 100:
        return page.decode()
    else:
        print ("ERROR: ycc.fr seem down?")
        return None


def getPage(s, p):
    conn = http.client.HTTPConnection(s, timeout=10)
    try:
        conn.request("GET", p)
    except socket.gaierror:
        print ("[%s] impossible de récupérer la page %s."%(s, p))
        return None

    res = conn.getresponse()
    data = res.read()

    conn.close()
    return (res.status, data)
