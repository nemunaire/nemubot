# coding=utf-8

import http.client
import time
import re
import _thread
import threading
from datetime import date
from datetime import datetime

from module_state import ModuleState

from .SiteSoutenances import SiteSoutenances
from .Delayed import Delayed

nemubotversion = 3.0

DELAYED = dict()

def help_tiny():
  """Line inserted in the response to the command !help"""
  return "EPITA ING1 defenses module"

def help_full():
  return "!soutenance: gives information about current defenses state\n!soutenance <who>: gives the date of the next defense of /who/.\n!soutenances <who>: gives all defense dates of /who/"

datas = None
THREAD = None
wait = list()

def parseanswer(msg):
  global THREAD, wait
  if msg.cmd[0] == "soutenance" or msg.cmd[0] == "soutenances":
    if THREAD is None:
      THREAD = _thread.start_new_thread (startSoutenance, (msg,))
    else:
      wait.append(msg)
    return True
  return False


def parseask(msg):
  if len(DELAYED) > 0 and msg.nick == msg.srv.partner:
    treat = False
    for part in msg.content.split(';'):
      if part is None:
        continue
      for d in DELAYED.keys():
        if DELAYED[d].res is None and part.find(DELAYED[d].name) >= 0:
          result = re.match(".* est (.*[^.])\.?", part)
          if result is not None:
            DELAYED[d].res = result.group(1)
            DELAYED[d].evt.set()
    return treat
  return False


def startSoutenance (msg):
  global datas, THREAD, wait

  #Starts by updating datas
  if datas is not None:
    datas = datas.update ()
  if datas is None:
    datas = SiteSoutenances(getPage().decode())

  if len(msg.cmd) == 1 or msg.cmd[1] == "next":
    soutenance = datas.findLast()
    if soutenance is None:
      msg.send_chn ("Il ne semble pas y avoir de soutenance pour le moment.")
    else:
      if soutenance.start > soutenance.hour:
        avre = "%s de *retard*"%msg.just_countdown(soutenance.start - soutenance.hour, 4)
      else:
        avre = "%s *d'avance*"%msg.just_countdown(soutenance.hour - soutenance.start, 4)
      msg.send_chn ("Actuellement à la soutenance numéro %d, commencée il y a %s avec %s."%(soutenance.rank, msg.just_countdown(datetime.now () - soutenance.start, 4), avre))

  elif msg.cmd[1] == "assistants" or msg.cmd[1] == "assistant" or msg.cmd[1] == "yaka" or msg.cmd[1] == "yakas" or msg.cmd[1] == "acu" or msg.cmd[1] == "acus":
    assistants = datas.findAssistants()
    if len(assistants) > 0:
      msg.send_chn ("Les %d assistants faisant passer les soutenances sont : %s." % (len(assistants), ', '.join(assistants.keys())))
    else:
      msg.send_chn ("Il ne semble pas y avoir de soutenance pour le moment.")
  else:
    name = msg.cmd[1]

    if msg.cmd[0] == "soutenance":
      soutenance = datas.findClose(name)
      if soutenance is None:
        global DELAYED
        DELAYED[msg] = Delayed(name)
        msg.srv.send_msg_prtn ("~whois %s" % name)
        DELAYED[msg].wait(5)
        if DELAYED[msg].res is not None:
          name = DELAYED[msg].res
          soutenance = datas.findClose(name)

      if soutenance is None:
        msg.send_chn ("Pas d'horaire de soutenance pour %s."%name)
      else:
        if soutenance.state == "En cours":
          msg.send_chn ("%s est actuellement en soutenance avec %s. Elle était prévue à %s, position %d."%(name, soutenance.assistant, soutenance.hour, soutenance.rank))
        elif soutenance.state == "Effectue":
          msg.send_chn ("%s a passé sa soutenance avec %s. Elle a duré %s."%(name, soutenance.assistant, msg.just_countdown(soutenance.end - soutenance.start, 4)))
        elif soutenance.state == "Retard":
          msg.send_chn ("%s était en retard à sa soutenance de %s."%(name, soutenance.hour))
        else:
          last = datas.findLast()
          if last is not None:
            if soutenance.hour + (last.start - last.hour) > datetime.now ():
              msg.send_chn ("Soutenance de %s : %s, position %d ; estimation du passage : dans %s."%(name, soutenance.hour, soutenance.rank, msg.just_countdown((soutenance.hour - datetime.now ()) + (last.start - last.hour))))
            else:
              msg.send_chn ("Soutenance de %s : %s, position %d ; passage imminent."%(name, soutenance.hour, soutenance.rank))
          else:
            msg.send_chn ("Soutenance de %s : %s, position %d."%(name, soutenance.hour, soutenance.rank))

    elif msg.cmd[0] == "soutenances":
      souts = datas.findAll(name)
      if souts is None:
        msg.send_snd ("Pas de soutenance prévues pour %s."%name)
      else:
        first = True
        for s in souts:
          if first:
            msg.send_snd ("Soutenance(s) de %s : - %s (position %d) ;"%(name, s.hour, s.rank))
            first = False
          else:
            msg.send_snd ("                  %s  - %s (position %d) ;"%(len(name)*' ', s.hour, s.rank))
  THREAD = None
  if len(wait) > 0:
    startSoutenance(wait.pop())


def getPage():
  conn = http.client.HTTPConnection(CONF.getNode("server")["ip"])
  try:
    conn.request("GET", CONF.getNode("server")["url"])

    res = conn.getresponse()
    data = res.read()
  except:
    print ("[%s] impossible de récupérer la page %s."%(s, p))
    return ""

  conn.close()
  return data
