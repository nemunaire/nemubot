# coding=utf-8

import re
import sys
from datetime import datetime

nemubotversion = 3.0

from module_state import ModuleState

def load():
  """Load this module"""
  global DATAS
  if not DATAS.hasNode("aliases"):
    DATAS.addChild(ModuleState("aliases"))
  DATAS.getNode("aliases").setIndex("alias")
  if not DATAS.hasNode("variables"):
    DATAS.addChild(ModuleState("variables"))
  DATAS.getNode("variables").setIndex("name")

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "alias module"

def help_full ():
  return "TODO"


def parseanswer (msg):
  global DATAS
  if msg.cmd[0] == "set":
    if len (msg.cmd) > 2:
      var = ModuleState("variable")
      var["name"] = msg.cmd[1]
      var["value"] = " ".join(msg.cmd[2:])
      DATAS.getNode("variables").addChild(var)
      msg.send_snd("Variable $%s définie." % msg.cmd[1])
      save()
    else:
      msg.send_snd("!set prend au minimum deux arguments : le nom de la variable et sa valeur.")
    return True
  elif msg.cmd[0] in DATAS.getNode("aliases").index:
    msg.content = msg.content.replace("!" + msg.cmd[0], DATAS.getNode("aliases").index[msg.cmd[0]]["origin"], 1)

    cnt = msg.content.split(' ')
    for i in range(0,len(cnt)):
      res = re.match("^([^a-zA-Z0-9]*)\\$([a-zA-Z0-9]+)(.*)$", cnt[i])
      if res is not None:
        if res.group(2) == "sender":
          cnt[i] = msg.sender
        elif res.group(2) == "chan" or res.group(2) == "channel":
          cnt[i] = msg.channel
        elif res.group(2) == "date":
          now = datetime.now()
          cnt[i] = ("%d/%d/%d %d:%d:%d"%(now.day, now.month, now.year, now.hour, now.minute, now.second))
        elif res.group(2) in DATAS.getNode("variables").index:
          cnt[i] = DATAS.getNode("variables").index[res.group(2)]["value"]
        else:
          cnt[i] = ""
        cnt[i] = res.group(1) + cnt[i] + res.group(3)
    msg.content = " ".join(cnt)
    msg.reparsemsg()
    return True
  else:
    return False


def parseask (msg):
  global ALIAS
  if re.match(".*(set|cr[ée]{2}|nouvel(le)?) alias.*", msg.content) is not None:
    result = re.match(".*alias !?([a-zA-Z0-9_-]+) (pour|=|:) (.+)$", msg.content)
    if result.group(1) in DATAS.getNode("aliases").index or result.group(3).find("alias") >= 0:
      msg.send_snd("Cet alias est déjà défini.")
    else:
      alias = ModuleState("alias")
      alias["alias"] = result.group(1)
      alias["origin"] = result.group(3)
      alias["creator"] = msg.sender
      DATAS.getNode("aliases").addChild(alias)
      msg.send_snd("Nouvel alias %s défini avec succès." % result.group(1))
      save()
    return True
  return False
