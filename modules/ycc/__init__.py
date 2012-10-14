# coding=utf-8

import http.client
import imp
import re
import sys

from . import Tinyfier

nemubotversion = 3.2

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Gets YCC urls"

def help_full ():
  return "!ycc [<url>]: with an argument, reduce the given <url> thanks to ycc.fr; without argument, reduce the last URL said on the current channel."

def load(context):
    Tinyfier.Response = Response

def reload():
    imp.reload(Tinyfier)
    Tinyfier.Response = Response

def cmd_ycc(msg):
    global LAST_URLS
    if len(msg.cmd) == 1:
        if msg.channel in LAST_URLS and len(LAST_URLS[msg.channel]) > 0:
            url = LAST_URLS[msg.channel].pop()
            t = Tinyfier.Tinyfier(url, msg)
            t.start()
        else:
            return Response(msg.sender, "je n'ai pas d'autre URL à réduire", msg.channel, nick=msg.nick)
    else:
        if len(msg.cmd) < 6:
            for url in msg.cmd[1:]:
                t = Tinyfier.Tinyfier(url, msg)
                t.start()
        else:
            return Response(msg.sender, "je ne peux pas réduire autant d'URL "
                         "d'un seul coup.", msg.channel, nick=msg.nick)
    return False

LAST_URLS = dict()

def parselisten(msg):
    global LAST_URLS
    if re.match(".*(https?://|www\.)[^ ]+.*", msg.content) is not None:
        res = re.match(".*(((ht|f)tps?://|www\.)[^ ]+).*", msg.content)
        if msg.channel not in LAST_URLS:
            LAST_URLS[msg.channel] = list()
        LAST_URLS[msg.channel].append(res.group(1))
        return True
    return False
