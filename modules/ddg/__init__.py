# coding=utf-8

import imp

nemubotversion = 3.0

from . import DDGSearch
from . import WFASearch

lastSearch = dict()

def load():
  global CONF
  WFASearch.CONF = CONF

def reload():
  imp.reload(DDGSearch)
  imp.reload(WFASearch)

def parseanswer(msg):
  global lastSearch
  req = None
  if msg.cmd[0] == "def" or msg.cmd[0] == "d" or msg.cmd[0] == "define" or msg.cmd[0] == "defini" or msg.cmd[0] == "definit" or msg.cmd[0] == "definition":
    req = "def"
  elif msg.cmd[0] == "g" or msg.cmd[0] == "ddg" or msg.cmd[0] == "d":
    req = "link"
  elif msg.cmd[0] == "wfa" or msg.cmd[0] == "calc" or msg.cmd[0] == "wa":
    req = "wfa"

  if msg.cmd[0] == "more" or msg.cmd[0] == "plus":
    if msg.channel in lastSearch and lastSearch[msg.channel] is not None:
      msg.send_chn(lastSearch[msg.channel].nextRes)
    else:
      msg.send_chn("There is no ongoing research.")
  elif req is not None:
    if len(msg.cmd) > 1:
      if req == "wfa":
        s = WFASearch.WFASearch(' '.join(msg.cmd[1:]))
        #print (s.wfares)
        if not s.success:
          msg.send_chn(s.error)
          return True
      else:
        s = DDGSearch.DDGSearch(' '.join(msg.cmd[1:]))

      if req == "def":
        msg.send_chn(s.definition)
      else:
        msg.send_chn(s.nextRes)
      lastSearch[msg.channel] = s
    else:
      msg.send_chn("What are you looking for?")
    return True

  return False


