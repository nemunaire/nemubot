# coding=utf-8

import http.client
import imp
import re
import sys

from . import Tinyfier

nemubotversion = 3.0

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Gets YCC urls"

def help_full ():
  return "!ycc [<url>]: with an argument, reduce the given <url> thanks to ycc.fr; without argument, reduce the last URL said on the current channel."

def reload():
  imp.reload(Tinyfier)

def parseanswer(msg):
  global LAST_URLS
  if msg.cmd[0] == "ycc":
    if len(msg.cmd) == 1:
      if msg.channel in LAST_URLS and len(LAST_URLS[msg.channel]) > 0:
        url = LAST_URLS[msg.channel].pop()
        t = Tinyfier.Tinyfier(url, msg)
        t.start()
      else:
        msg.send_chn("%s: je n'ai pas d'autre URL  reduire" % msg.sender)
    else:
      if len(msg.cmd) < 6:
        for url in msg.cmd[1:]:
          t = Tinyfier.Tinyfier(url, msg)
          t.start()
      else:
        msg.send_chn("%s: je ne peux pas réduire autant d'URL d'un seul coup." % msg.sender)
    return True
  else:
    return False

LAST_URLS = dict()

def parselisten (msg):
  global LAST_URLS
  if re.match(".*(https?://|www\.)[^ ]+.*", msg.content) is not None:
    res = re.match(".*(((ht|f)tps?://|www\.)[^ ]+).*", msg.content)
    if msg.channel in LAST_URLS:
      LAST_URLS[msg.channel].append(res.group(1))
    else:
      LAST_URLS[msg.channel] = list(res.group(1))
    return True
  return False
