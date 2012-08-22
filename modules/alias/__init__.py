# coding=utf-8

import re
import sys
from datetime import datetime

nemubotversion = 3.2

from xmlparser.node import ModuleState

CONTEXT = None

def load(context):
    """Load this module"""
    global CONTEXT
    CONTEXT = context

    from hooks import Hook
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(cmd_set, "set"))
    context.hooks.add_hook(context.hooks.all_pre, Hook(treat_variables))

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

def set_variable(name, value):
    var = ModuleState("variable")
    var["name"] = name
    var["value"] = value
    DATAS.getNode("variables").addChild(var)

def get_variable(name, msg=None):
    if name == "sender":
        return msg.sender
    elif name == "nick":
        return msg.nick
    elif name == "chan" or name == "channel":
        return msg.channel
    elif name == "date":
        now = datetime.now()
        return ("%d/%d/%d %d:%d:%d"%(now.day, now.month, now.year, now.hour,
                                     now.minute, now.second))
    elif name in DATAS.getNode("variables").index:
        return DATAS.getNode("variables").index[name]["value"]
    else:
        return ""

def cmd_set(msg):
    if len (msg.cmd) > 2:
        set_variable(msg.cmd[1], " ".join(msg.cmd[2:]))
        msg.send_snd("Variable $%s définie." % msg.cmd[1])
        save()
        return True
    else:
        msg.send_snd("!set prend au minimum deux arguments : le nom de la variable et sa valeur.")
    return False


def treat_variables(msg):
    if msg.cmd[0] != "set" and re.match(".*(set|cr[ée]{2}|nouvel(le)?) alias.*", msg.content) is None:
        cnt = msg.content.split(' ')
        for i in range(0, len(cnt)):
            res = re.match("^([^a-zA-Z0-9]*)\\$([a-zA-Z0-9]+)(.*)$", cnt[i])
            if res is not None:
                cnt[i] = res.group(1) + get_variable(res.group(2), msg) + res.group(3)
        msg.content = " ".join(cnt)
        return True
    return False


def parseanswer(msg):
    if msg.cmd[0] in DATAS.getNode("aliases").index:
        msg.content = msg.content.replace("!" + msg.cmd[0], DATAS.getNode("aliases").index[msg.cmd[0]]["origin"], 1)
        msg.reparsemsg()
        return True
    return False


def parseask(msg):
  global ALIAS
  if re.match(".*(set|cr[ée]{2}|nouvel(le)?) alias.*", msg.content) is not None:
    result = re.match(".*alias !?([^ ]+) (pour|=|:) (.+)$", msg.content)
    if result.group(1) in DATAS.getNode("aliases").index or result.group(3).find("alias") >= 0:
      msg.send_snd("Cet alias est déjà défini.")
    else:
      alias = ModuleState("alias")
      alias["alias"] = result.group(1)
      alias["origin"] = result.group(3)
      alias["creator"] = msg.nick
      DATAS.getNode("aliases").addChild(alias)
      msg.send_snd("Nouvel alias %s défini avec succès." % result.group(1))
      save()
    return True
  return False
