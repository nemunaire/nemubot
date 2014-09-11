# coding=utf-8

"""URL reducer module"""

import re
from urllib.parse import urlparse
from urllib.parse import quote
from urllib.request import urlopen

from hooks import hook

nemubotversion = 3.4

def help_full():
    return "!ycc [<url>]: with an argument, reduce the given <url> thanks to ycc.fr; without argument, reduce the last URL said on the current channel."

LAST_URLS = dict()

def gen_response(res, msg, srv):
    if res is None:
        raise IRCException("la situation est embarassante, il semblerait que YCC soit down :(")
    elif isinstance(res, str):
        return Response(msg.sender, "URL pour %s : %s" % (srv, res), msg.channel)
    else:
        raise IRCException("mauvaise URL : %s" % srv)

@hook("cmd_hook", "ycc")
def cmd_ycc(msg):
    if len(msg.cmds) == 1:
        global LAST_URLS
        if msg.channel in LAST_URLS and len(LAST_URLS[msg.channel]) > 0:
            msg.cmds.append(LAST_URLS[msg.channel].pop())
        else:
            raise IRCException("je n'ai pas d'autre URL à réduire.")

    if len(msg.cmds) > 5:
        raise IRCException("je ne peux pas réduire autant d'URL d'un seul coup.")

    res = list()
    for url in msg.cmds[1:]:
        o = urlparse(url, "http")
        if o.scheme != "":
            snd_url = "http://ycc.fr/redirection/create/" + quote(url, "/:%@&=?")
            print_debug(snd_url)
            raw = urlopen(snd_url, timeout=10)
            if o.netloc == "":
                res.append(gen_response(raw.read().decode(), msg, o.scheme))
            else:
                res.append(gen_response(raw.read().decode(), msg, o.netloc))
        else:
            res.append(gen_response(False, msg, url))
    return res

@hook("msg_default")
def parselisten(msg):
    parseresponse(msg)
    return None

@hook("all_post")
def parseresponse(msg):
    global LAST_URLS
    try:
      urls = re.findall("([a-zA-Z0-9+.-]+:(?://)?[^ ]+)", msg.text)
      for url in urls:
          o = urlparse(url)
          if o.scheme != "":
              if o.netloc == "ycc.fr" or (o.netloc == "" and len(o.path) < 10):
                  continue
              if msg.channel not in LAST_URLS:
                  LAST_URLS[msg.channel] = list()
              LAST_URLS[msg.channel].append(url)
    except:
        pass
    return msg
