# coding=utf-8

import re
import time
import sys
from datetime import timedelta
from datetime import datetime
from datetime import date
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation

filename = ""
channels = "#nemutest #42sh #epitagueule"
MANCHE = None
SCORES = dict ()
temps = dict ()

class Score:
  def __init__(self):
    #FourtyTwo
    self.ftt = 0
    #TwentyThree
    self.twt = 0
    self.pi = 0
    self.notfound = 0
    self.tententen = 0
    self.leet = 0
    self.great = 0
    self.bad = 0
    self.last = None
    self.changed = False

  def parse(self, item):
    self.ftt = int(item.getAttribute("fourtytwo"))
    self.twt = int(item.getAttribute("twentythree"))
    self.pi = int(item.getAttribute("pi"))
    self.notfound = int(item.getAttribute("notfound"))
    self.tententen = int(item.getAttribute("tententen"))
    self.leet = int(item.getAttribute("leet"))
    self.great = int(item.getAttribute("great"))
    self.bad = int(item.getAttribute("bad"))

  def merge(self, other):
    self.ftt += other.ftt
    self.twt += other.twt
    self.pi += other.pi
    self.notfound += other.notfound
    self.tententen += other.tententen
    self.leet += other.leet
    self.great += other.great
    self.bad += other.bad

  def newWinner(self):
    self.ftt = 0
    self.twt = 0
    self.pi = 1
    self.notfound = 1
    self.tententen = 0
    self.leet = 1
    self.great = -1
    self.bad = -4

  def isWinner(self):
    return self.great >= 42

  def playFtt(self):
    if self.canPlay():
      self.ftt += 1
  def playTwt(self):
    if self.canPlay():
      self.twt += 1
  def playPi(self):
    if self.canPlay():
      self.pi += 1
  def playNoutfound(self):
    if self.canPlay():
      self.notfound += 1
  def playTen(self):
    if self.canPlay():
      self.tententen += 1
  def playLeet(self):
    if self.canPlay():
      self.leet += 1
  def playGreat(self):
    if self.canPlay():
      self.great += 1
  def playBad(self):
    if self.canPlay():
      self.bad += 1

  def toTuple(self):
    return (self.ftt, self.twt, self.pi, self.notfound, self.tententen, self.leet, self.great, self.bad)

  def canPlay(self):
    self.changed = True
    return self.last == None or self.last.minute != datetime.now().minute or self.last.hour != datetime.now().hour or self.last.day != datetime.now().day

  def hasChanged(self):
    if self.changed:
      self.changed = False
      self.last = datetime.now()
      return True
    else:
      return False

  def score(self):
    return (self.ftt * 2 - self.bad * 10 + self.great * 5 + self.leet * 3 + self.pi * 3.1415 + self.twt + self.notfound * 4.04)

  def details(self):
    return "42: %d, 23: %d, bad: %d, great: %d, leet: %d, pi: %d, 404: %d, 10: %d = %d."%(self.ftt, self.twt, self.bad, self.great, self.leet, self.pi, self.notfound, self.tententen, self.score())


def xmlparse(node):
  """Parse the given node and add scores to the global list."""
  global SCORES, MANCHE
  for item in node.getElementsByTagName("score"):
    SCORES[item.getAttribute("name")] = Score ()
    SCORES[item.getAttribute("name")].parse(item)

  manche = node.getElementsByTagName("manche")[0]
  MANCHE = (int(manche.getAttribute("number")),
            manche.getAttribute("winner"),
            int(manche.getAttribute("winner_score")),
            manche.getAttribute("who"),
#            datetime.now ())
            datetime.fromtimestamp (time.mktime (time.strptime (manche.getAttribute("date")[:19], "%Y-%m-%d %H:%M:%S"))))

def load_module(datas_path):
  """Load this module"""
  global MANCHE, SCORES, filename
  MANCHE = None
  SCORES = dict ()
  filename = datas_path + "/42.xml"

  sys.stdout.write ("Loading 42scores ... ")
  dom = parse(filename)
  xmlparse (dom.documentElement)
  print ("done (%d loaded, currently in round %d)" % (len(SCORES), -42))

def save_module():
  """Save the scores"""
  global filename
  sys.stdout.write ("Saving 42scores ... ")

  impl = getDOMImplementation()
  newdoc = impl.createDocument(None, 'game', None)
  top = newdoc.documentElement

  for name in SCORES.keys():
    scr = 'fourtytwo="%d" twentythree="%d" pi="%d" notfound="%d" tententen="%d" leet="%d" great="%d" bad="%d"'% SCORES[name].toTuple()
    item = parseString ('<score name="%s" %s />' % (name, scr)).documentElement
    top.appendChild(item);

  top.appendChild(parseString ('<manche number="%d" winner="%s" winner_score="%d" who="%s" date="%s" />' % MANCHE).documentElement)

  with open(filename, "w") as f:
    newdoc.writexml (f)
  print ("done")


def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "42 game!"

def help_full ():
  return "!42: display scores\n!42 help: display the performed calculate\n!42 manche: display information about current round\n!42 /who/: show the /who/'s scores"


def rev (tupl):
  (k, v) = tupl
  return (v.score(), k)

def parseanswer (msg):
  if msg.cmd[0] == "42" or msg.cmd[0] == "score" or msg.cmd[0] == "scores":
    global SCORES, MANCHE
    if len(msg.cmd) > 3 and msg.is_owner and (msg.cmd[1] == "merge"):
      if msg.cmd[2] in SCORES and msg.cmd[3] in SCORES:
        SCORES[msg.cmd[2]].merge (SCORES[msg.cmd[3]])
        del SCORES[msg.cmd[3]]
        msg.send_chn ("%s a été correctement fusionné avec %s."%(msg.cmd[3], msg.cmd[2]))
      else:
        if msg.cmd[2] not in SCORES:
          msg.send_chn ("%s n'est pas un joueur connu."%msg.cmd[2])
        elif msg.cmd[3] not in SCORES:
          msg.send_chn ("%s n'est pas un joueur connu."%msg.cmd[3])
    elif len(msg.cmd) > 1 and (msg.cmd[1] == "help" or msg.cmd[1] == "aide"):
      msg.send_chn ("Formule : normal * 2 - bad * 10 + great * 5 + leet * 3 + pi * 3.1415 + dt + not_found * 4.04")
    elif len(msg.cmd) > 1 and (msg.cmd[1] == "manche" or msg.cmd[1] == "round"):
      msg.send_chn ("Nous sommes dans la %de manche, gagnée par %s avec %d points et commencée par %s le %s"%MANCHE)
  #elif where == "#nemutest":
    else:
      phrase = ""

      if len(msg.cmd) > 1:
        if msg.cmd[1] in SCORES:
          phrase += " " + msg.cmd[1] + ": " + SCORES[msg.cmd[1]].details()
        else:
          phrase = " %s n'a encore jamais joué,"%(msg.cmd[1])
      else:
        for nom, scr in sorted(SCORES.items(), key=rev, reverse=True):
          score = scr.score()
          if score != 0:
            if phrase == "":
              phrase = " *%s: %d*,"%(nom, score)
            else:
              phrase += " %s: %d,"%(nom, score)

      msg.send_chn ("Scores :%s" % (phrase[0:len(phrase)-1]))
    return True
  else:
    return False


def win(msg):
  global SCORES, MANCHE
  who = msg.sender

  (num_manche, winner, nb_points, whosef, dayte) = MANCHE

  maxi_scor = 0
  maxi_name = None

  for player in SCORES.keys():
    scr = SCORES[player].score()
    if scr > maxi_scor:
      maxi_scor = scr
      maxi_name = player

  #Reset !
  SCORES = dict()
#  SCORES[maxi_name] = (-10, 0, -4, 0, 0, -2, 0)
#  SCORES[maxi_name] = (0, 0, 0, 0, 0, 0, 0)
  SCORES[who].newWinner()

  if who != maxi_name:
    msg.send_chn ("Félicitations %s, tu remportes cette manche terminée par %s, avec un score de %d !"%(maxi_name, who, maxi_scor))
  else:
    msg.send_chn ("Félicitations %s, tu remportes cette manche avec %d points !"%(maxi_name, maxi_scor))

  MANCHE = (num_manche + 1, maxi_name, maxi_scor, who, datetime.now ())

  print ("Nouvelle manche :", MANCHE)
  save_module ()


def parseask (msg):
  return False


def getUser(name):
  global SCORES
  if name not in SCORES:
    SCORES[name] = Score()
  return SCORES[name]
    

def parselisten (msg):
#  if msg.channel == "#nemutest":
  if msg.channel != "#nemutest":
    if (msg.content.strip().startswith("42") and len (msg.content) < 5) or ((msg.content.strip().lower().startswith("quarante-deux") or msg.content.strip().lower().startswith("quarante deux")) and len (msg.content) < 17):
      if msg.time.minute == 10 and msg.time.second == 10 and msg.time.hour == 10:
        getUser(msg.sender).playTen()
        getUser(msg.sender).playGreat()
      elif msg.time.minute == 42:
        if msg.time.second == 0:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playFtt()
      else:
        getUser(msg.sender).playBad()

    if (msg.content.strip().startswith("23") and len (msg.content) < 5) or ((msg.content.strip().lower().startswith("vingt-trois") or msg.content.strip().lower().startswith("vingt trois")) and len (msg.content) < 14):
      if msg.time.minute == 23:
        if msg.time.second == 0:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playTwt()
      else:
        getUser(msg.sender).playBad()

    if (msg.content.strip().startswith("101010") and len (msg.content) < 9):
      if msg.time.minute == 10 and msg.time.hour == 10:
        if msg.time.second == 10:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playTen()
      else:
        getUser(msg.sender).playBad()

    if (msg.content.strip().startswith("12345") and len (msg.content) < 8) or (msg.content.strip().startswith("012345") and len (msg.content) < 9):
      if msg.time.hour == 1 and msg.time.minute == 23 and msg.time.second == 45:
        getUser(msg.sender).playGreat()
        getUser(msg.sender).playTwt()
      else:
        getUser(msg.sender).playBad()

    if len (msg.content) < 12 and (msg.content.strip().lower().startswith("leet time") or msg.content.strip().lower().startswith("leettime") or msg.content.strip().lower().startswith("leetime") or msg.content.strip().lower().startswith("l33t time") or msg.content.strip().lower().startswith("1337")):
      if msg.time.hour == 13 and msg.time.minute == 37:
        if msg.time.second == 0:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playLeet()
      else:
        getUser(msg.sender).playBad()

    if len (msg.content) < 11 and (msg.content.strip().lower().startswith("pi time") or msg.content.strip().lower().startswith("pitime") or msg.content.strip().lower().startswith("3.14 time")):
      if msg.time.hour == 3 and msg.time.minute == 14:
        if msg.time.second == 15 or msg.time.second == 16:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playPi()
      else:
        getUser(msg.sender).playBad()

    if len (msg.content) < 16 and (msg.content.strip().lower().startswith("time not found") or msg.content.strip().lower().startswith("timenotfound") or msg.content.strip().lower().startswith("404 time")) or (len (msg.content) < 6 and msg.content.strip().lower().startswith("404")):
      if msg.time.hour == 4 and msg.time.minute == 4:
        if msg.time.second == 0 or msg.time.second == 4:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playNotfound()
      else:
        getUser(msg.sender).playBad()

    if getUser(msg.sender).isWinner():
      print ("Nous avons un vainqueur ! Nouvelle manche :p")
      win(msg)
    elif getUser(msg.sender).hasChanged():
      save_module ()
  return False
