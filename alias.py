# coding=utf-8

import re
import sys
from datetime import datetime
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation

filename = ""
ALIAS = {}
variables = {}

def load_module(datas_path):
  """Load this module"""
  global ALIAS, filename
  SCORES = dict ()
  filename = datas_path + "/alias.xml"

  sys.stdout.write ("Loading aliaslist ... ")
  dom = parse(filename)
  for item in dom.documentElement.getElementsByTagName("alias"):
    ALIAS[item.getAttribute("alias")] = item.getAttribute("origin")
  for item in dom.documentElement.getElementsByTagName("variable"):
    variables[item.getAttribute("name")] = item.getAttribute("value")
  print ("done (%d aliases and %d vars)" % (len(ALIAS), len (variables)))

def save_module():
  """Save the aliases"""
  global ALIAS, variables, filename
  sys.stdout.write ("Saving aliases ... ")

  impl = getDOMImplementation()
  newdoc = impl.createDocument(None, 'aliaslist', None)
  top = newdoc.documentElement

  for name in ALIAS.keys():
    item = newdoc.createElement("alias")
    item.setAttribute("alias", name)
    item.setAttribute("origin", ALIAS[name])
    top.appendChild(item);

  for name in variables.keys():
    item = newdoc.createElement("variable")
    item.setAttribute("name", name)
    item.setAttribute("value", variables[name])
    top.appendChild(item);

  with open(filename, "w") as f:
    newdoc.writexml (f)
  print ("done")


def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "alias module"

def help_full ():
  return "TODO"


def parseanswer (msg):
  global ALIAS, variables
  if msg.cmd[0] == "set":
    if len (msg.cmd) > 2:
      variables[msg.cmd[1]] = " ".join(msg.cmd[2:])
      msg.send_snd("Variable $%s définie." % msg.cmd[1])
    else:
      msg.send_snd("!set prend au minimum deux arguments : le nom de la variable et sa valeur.")
    return True
  elif msg.cmd[0] in ALIAS:
    msg.content = msg.content.replace("!" + msg.cmd[0], ALIAS[msg.cmd[0]], 1)

    cnt = msg.content.split(' ')
    for i in range(0,len(cnt)):
      if len (cnt[i]) and cnt[i][0] == '$':
        if cnt[i][1] == '$' and len(cnt[i]) == 2:
          cnt[i] = "$"
        elif cnt[i] == "$sender":
          cnt[i] = msg.sender
        elif cnt[i] == "$chan" or cnt[i] == "$channel":
          cnt[i] = msg.channel
        elif cnt[i] == "$date":
          now = datetime.now()
          cnt[i] = ("%d/%d/%d %d:%d:%d"%(now.day, now.month, now.year, now.hour, now.minute, now.second))
        elif cnt[i] == "$date,":
          now = datetime.now()
          cnt[i] = ("%d/%d/%d %d:%d:%d,"%(now.day, now.month, now.year, now.hour, now.minute, now.second))
        elif cnt[i] == "$date.":
          now = datetime.now()
          cnt[i] = ("%d/%d/%d %d:%d:%d."%(now.day, now.month, now.year, now.hour, now.minute, now.second))
        elif cnt[i][1:] in variables:
          cnt[i] = variables[cnt[i][1:]]
        else:
          cnt[i] = ""
    msg.content = " ".join(cnt)
    msg.reparsemsg()
    return True
  else:
    return False


def parseask (msg):
  global ALIAS
  if re.match(".*(set|cr[ée]{2}|nouvel(le)?) alias.*", msg.content) is not None:
    result = re.match(".*alias !?([a-zA-Z0-9_-]+) (pour|=|:) (.+)$", msg.content)
    if result.group(1) in ALIAS or result.group(3).find("alias") >= 0:
      msg.send_snd("Cet alias est déjà défini.")
    else:
      ALIAS[result.group(1)] = result.group(3)
      msg.send_snd("Nouvel alias %s défini avec succès." % result.group(1))
    return True
  return False


def parselisten (msg):
  return False
