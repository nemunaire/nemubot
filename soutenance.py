# coding=utf-8

import http.client
import time
import re
from datetime import date
from datetime import datetime
from datetime import timedelta

stack = list()

def getPage ():
  conn = http.client.HTTPSConnection("intra.acu.epita.fr")
  conn.request("GET", "/intra/sout_liste.html")

  res = conn.getresponse()
  data = res.read()

  conn.close()
  return data

class Soutenance:
  def __init__(self):
    self.hour = None
    self.rank = 0
    self.login = None
    self.state = None
    self.assistant = None
    self.start = None
    self.end = None

class SiteSoutenances:
  def __init__(self, page):
    save = False
    self.souts = list()
    self.updated = datetime.now ()
    last = None
    for line in page.split("\n"):
      if re.match("</tr>", line) is not None:
        save = False
      elif re.match("<tr.*>", line) is not None:
        save = True
        last = Soutenance()
        self.souts.append(last)
      elif save:
        result = re.match("<td[^>]+>(.*)</td>", line)
        if last.hour is None:
          try:
            last.hour = datetime.fromtimestamp (time.mktime (time.strptime (result.group(1), "%Y-%m-%d  %H:%M")))
          except ValueError:
            continue
        elif last.rank == 0:
          last.rank = int (result.group(1))
        elif last.login == None:
          last.login = result.group(1)
        elif last.state == None:
          last.state = result.group(1)
        elif last.assistant == None:
          last.assistant = result.group(1)
        elif last.start == None:
          try:
            last.start = datetime.fromtimestamp (time.mktime (time.strptime (result.group(1), "%Y-%m-%d  %H:%M")))
          except ValueError:
            last.start = None
        elif last.end == None:
          try:
            last.end = datetime.fromtimestamp (time.mktime (time.strptime (result.group(1), "%Y-%m-%d  %H:%M")))
          except ValueError:
            last.end = None
          
  def update(self):
    if self.findLast() is not None and datetime.now () - self.updated > timedelta(minutes=2):
      return None
    elif datetime.now () - self.updated < timedelta(hours=1):
      return self
    else:
      return None

  def findAssistants(self):
    h = {}
    for s in self.souts:
      if s.assistant is not None and s.assistant != "":
        h[s.assistant] = (s.start, s.end)
    return h
    

  def findLast(self):
    close = None
    for s in self.souts:
      if s.state != "En attente" and s.start is not None and (close is None or close.rank < s.rank or close.hour.day > s.hour.day):
        close = s
    return close

  def findAll(self, login):
    ss = list()
    for s in self.souts:
      if s.login == login:
        ss.append(s)
    return ss

  def findClose(self, login):
    ss = self.findAll(login)
    close = None
    for s in ss:
      if close is not None:
        print (close.hour)
      print (s.hour)
      if close is None or (close.hour < s.hour and close.hour.day >= datetime.datetime().day):
        close = s
    return close


def load_module(datas_path):
  """Load this module"""
  return

def save_module():
  """Save the module state"""
  return

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return None

def help_full ():
  return None

datas = None

def parseanswer (msg):
  global datas
  if msg.cmd[0] == "soutenance" or msg.cmd[0] == "soutenances":
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

    return True
  return False

def parseask (msg):
  return False

def parselisten (msg):
  return False


def startThread(site):
  site.check ()
