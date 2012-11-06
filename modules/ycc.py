# coding=utf-8

import re

from tools import web

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
            srv = web.getHost(url)
            if srv is not None:
                res.append(gen_response(
                    web.getURLContent("http://ycc.fr/redirection/create/"
                                      + url).decode(), msg, srv))
            else:
                res.append(gen_response(False, msg, url))
        return res
    else:
        return Response(msg.sender, "je ne peux pas réduire autant d'URL "
                     "d'un seul coup.", msg.channel, nick=msg.nick)

def parselisten(msg):
    global LAST_URLS
    res = re.match(".*([a-zA-Z0-9+.-]+):(//)?([^ ]*).*", msg.content)
    if res is not None:
        url = res.group(1)
        srv = web.getHost(url)
        if srv is not None:
            if srv == "ycc.fr":
                return False
            if msg.channel not in LAST_URLS:
                LAST_URLS[msg.channel] = list()
            LAST_URLS[msg.channel].append(url)
            return True
    return False

def parseresponse(res):
    parselisten(res)
    return True
