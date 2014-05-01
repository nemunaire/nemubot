# coding=utf-8

import re
from urllib.parse import urlparse
from urllib.parse import quote
from urllib.request import urlopen

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
            o = urlparse(url, "http")
            if o.scheme != "":
                snd_url = "http://ycc.fr/redirection/create/" + quote(url, "/:%#@&=?")
                print_debug(snd_url)
                raw = urlopen(snd_url, timeout=10)
                if o.netloc == "":
                    res.append(gen_response(raw.read().decode(), msg, o.scheme))
                else:
                    res.append(gen_response(raw.read().decode(), msg, o.netloc))
            else:
                res.append(gen_response(False, msg, url))
        return res
    else:
        return Response(msg.sender, "je ne peux pas réduire autant d'URL "
                     "d'un seul coup.", msg.channel, nick=msg.nick)

def parselisten(msg):
    global LAST_URLS
    try:
      urls = re.findall("([a-zA-Z0-9+.-]+:(?://)?[^ ]+)", msg.content)
      for url in urls:
          o = urlparse(url)
          if o.scheme != "":
              if o.netloc == "ycc.fr" or (o.netloc == "" and len(o.path) < 10):
                  continue
              if msg.channel not in LAST_URLS:
                  LAST_URLS[msg.channel] = list()
              LAST_URLS[msg.channel].append(o.geturl())
    except:
      pass
    return False

def parseresponse(res):
    parselisten(res)
    return True
