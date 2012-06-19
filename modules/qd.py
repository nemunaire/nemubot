# coding=utf-8

import re
import time
import random
import sys
import threading
from datetime import timedelta
from datetime import datetime
from datetime import date

from module_state import ModuleState
from wrapper import Wrapper

nemubotversion = 3.0

channels = "#nemutest #42sh #ykar #epitagueule"
LASTSEEN = dict ()
temps = dict ()

SCORES = None

def load():
  global DATAS, SCORES
  DATAS.setIndex("name", "player")
  SCORES = QDWrapper()

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "42 game!"

def help_full ():
  return "!42: display scores\n!42 help: display the performed calculate\n!42 manche: display information about current round\n!42 /who/: show the /who/'s scores"


class QDWrapper(Wrapper):
  def __init__(self):
    global DATAS
    Wrapper.__init__(self)
    self.DATAS = DATAS
    self.stateName = "player"
    self.attName = "name"

  def __getitem__(self, i):
    if i in self.cache:
      return self.cache[i]
    else:
      sc = Score()
      sc.parse(Wrapper.__getitem__(self, i))
      self.cache[i] = sc
      return sc

class Score:
  """Manage the user's scores"""
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
    self.triche = 0
    self.last = None
    self.changed = False

  def parse(self, item):
    self.ftt = item.getInt("fourtytwo")
    self.twt = item.getInt("twentythree")
    self.pi = item.getInt("pi")
    self.notfound = item.getInt("notfound")
    self.tententen = item.getInt("tententen")
    self.leet = item.getInt("leet")
    self.great = item.getInt("great")
    self.bad = item.getInt("bad")
    self.triche = item.getInt("triche")

  def save(self, state):
    state.setAttribute("fourtytwo", self.ftt)
    state.setAttribute("twentythree", self.twt)
    state.setAttribute("pi", self.pi)
    state.setAttribute("notfound", self.notfound)
    state.setAttribute("tententen", self.tententen)
    state.setAttribute("leet", self.leet)
    state.setAttribute("great", self.great)
    state.setAttribute("bad", self.bad)
    state.setAttribute("triche", self.triche)

  def merge(self, other):
    self.ftt += other.ftt
    self.twt += other.twt
    self.pi += other.pi
    self.notfound += other.notfound
    self.tententen += other.tententen
    self.leet += other.leet
    self.great += other.great
    self.bad += other.bad
    self.triche += other.triche

  def newWinner(self):
    self.ftt = 0
    self.twt = 0
    self.pi = 1
    self.notfound = 1
    self.tententen = 0
    self.leet = 1
    self.great = -1
    self.bad = -4
    self.triche = 0

  def isWinner(self):
    return self.great >= 42

  def playFtt(self):
    if self.canPlay():
      self.ftt += 1
  def playTwt(self):
    if self.canPlay():
      self.twt += 1
  def playSuite(self):
    self.canPlay()
    self.twt += 1
    self.great += 1
  def playPi(self):
    if self.canPlay():
      self.pi += 1
  def playNotfound(self):
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
      self.great += 1
  def playTriche(self):
    self.triche += 1
  def oupsTriche(self):
    self.triche -= 1
  def bonusQuestion(self):
    return

  def toTuple(self):
    return (self.ftt, self.twt, self.pi, self.notfound, self.tententen, self.leet, self.great, self.bad, self.triche)

  def canPlay(self):
    ret = self.last == None or self.last.minute != datetime.now().minute or self.last.hour != datetime.now().hour or self.last.day != datetime.now().day
    self.changed = self.changed or ret
    return ret

  def hasChanged(self):
    if self.changed:
      self.changed = False
      self.last = datetime.now()
      return True
    else:
      return False

  def score(self):
    return (self.ftt * 2 + self.great * 5 + self.leet * 13.37 + (self.pi + 1) * 3.1415 * (self.notfound + 1) + self.tententen * 10 + self.twt - (self.bad + 1) * 10 * (self.triche * 5 + 1) + 7)

  def details(self):
    return "42: %d, 23: %d, leet: %d, pi: %d, 404: %d, 10: %d, great: %d, bad: %d, triche: %d = %d."%(self.ftt, self.twt, self.leet, self.pi, self.notfound, self.tententen, self.great, self.bad, self.triche, self.score())


def rev (tupl):
  (k, v) = tupl
  return (v.score(), k)

def parseanswer (msg):
  if msg.cmd[0] == "42" or msg.cmd[0] == "score" or msg.cmd[0] == "scores":
    global SCORES
    if len(msg.cmd) > 2 and msg.is_owner and ((msg.cmd[1] == "merge" and len(msg.cmd) > 3) or msg.cmd[1] == "oupstriche"):
      if msg.cmd[2] in SCORES and (len(msg.cmd) <= 3 or msg.cmd[3] in SCORES):
        if msg.cmd[1] == "merge":
          SCORES[msg.cmd[2]].merge (SCORES[msg.cmd[3]])
          del SCORES[msg.cmd[3]]
          msg.send_chn ("%s a été correctement fusionné avec %s."%(msg.cmd[3], msg.cmd[2]))
        elif msg.cmd[1] == "oupstriche":
          SCORES[msg.cmd[2]].oupsTriche()
      else:
        if msg.cmd[2] not in SCORES:
          msg.send_chn ("%s n'est pas un joueur connu."%msg.cmd[2])
        elif msg.cmd[3] not in SCORES:
          msg.send_chn ("%s n'est pas un joueur connu."%msg.cmd[3])
    elif len(msg.cmd) > 1 and (msg.cmd[1] == "help" or msg.cmd[1] == "aide"):
      msg.send_chn ("Formule : \"42\" * 2 + great * 5 + leet * 13.37 + (pi + 1) * 3.1415 * (not_found + 1) + tententen * 10 + \"23\" - (bad + 1) * 10 * (triche * 5 + 1) + 7")
    elif len(msg.cmd) > 1 and (msg.cmd[1] == "manche" or msg.cmd[1] == "round"):
      manche = DATAS.getNode("manche")
      msg.send_chn ("Nous sommes dans la %de manche, gagnée par %s avec %d points et commencée par %s le %s." % (manche.getInt("number"), manche["winner"], manche.getInt("winner_score"), manche["who"], manche.getDate("date")))
    #elif msg.channel == "#nemutest":
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
              phrase = " *%s.%s: %d*,"%(nom[0:1], nom[1:len(nom)], score)
            else:
              phrase += " %s.%s: %d,"%(nom[0:1], nom[1:len(nom)], score)

      msg.send_chn ("Scores :%s" % (phrase[0:len(phrase)-1]))
    return True
  else:
    return False


def win(msg):
  global SCORES
  who = msg.sender

  manche = DATAS.getNode("manche")

  maxi_scor = 0
  maxi_name = None

  for player in DATAS.index.keys():
    scr = SCORES[player].score()
    if scr > maxi_scor:
      maxi_scor = scr
      maxi_name = player

  for player in DATAS.index.keys():
    scr = SCORES[player].score()
    if scr > maxi_scor / 3:
      del SCORES[player]
    else:
      DATAS.index[player]["great"] = 0
  SCORES.flush()

  if who != maxi_name:
    msg.send_chn ("Félicitations %s, tu remportes cette manche terminée par %s, avec un score de %d !"%(maxi_name, who, maxi_scor))
  else:
    msg.send_chn ("Félicitations %s, tu remportes cette manche avec %d points !"%(maxi_name, maxi_scor))

  manche.setAttribute("number", manche.getInt("number") + 1)
  manche.setAttribute("winner", maxi_name)
  manche.setAttribute("winner_score", maxi_scor)
  manche.setAttribute("who", who)
  manche.setAttribute("date", datetime.now())

  print ("Nouvelle manche !")
  save()


def parseask (msg):
  if len(DELAYED) > 0:
    if msg.sender in DELAYED:
      DELAYED[msg.sender].msg = msg.content
      DELAYED[msg.sender].delayEvnt.set()
      return True
  return False


def getUser(name):
  global SCORES
  if name not in SCORES:
    SCORES[name] = Score()
  return SCORES[name]
    

def parselisten (msg):
  if len(DELAYED) > 0 and msg.sender in DELAYED and DELAYED[msg.sender].good(msg.content):
    msg.send_chn("%s: n'oublie pas le nemubot: devant ta réponse pour qu'elle soit prise en compte !" % msg.sender)

  bfrseen = None
  if msg.realname in LASTSEEN:
    bfrseen = LASTSEEN[msg.realname]
  LASTSEEN[msg.realname] = datetime.now()

#  if msg.channel == "#nemutest" and msg.sender not in DELAYED:
  if msg.channel != "#nemutest" and msg.sender not in DELAYED:

    if re.match("^(42|quarante[- ]?deux).{,2}$", msg.content.strip().lower()):
      if msg.time.minute == 10 and msg.time.second == 10 and msg.time.hour == 10:
        getUser(msg.sender).playTen()
        getUser(msg.sender).playGreat()
      elif msg.time.minute == 42:
        if msg.time.second == 0:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playFtt()
      else:
        getUser(msg.sender).playBad()

    if re.match("^(23|vingt[ -]?trois).{,2}$", msg.content.strip().lower()):
      if msg.time.minute == 23:
        if msg.time.second == 0:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playTwt()
      else:
        getUser(msg.sender).playBad()

    if re.match("^(10){3}.{,2}$", msg.content.strip().lower()):
      if msg.time.minute == 10 and msg.time.hour == 10:
        if msg.time.second == 10:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playTen()
      else:
        getUser(msg.sender).playBad()

    if re.match("^0?12345.{,2}$", msg.content.strip().lower()):
      if msg.time.hour == 1 and msg.time.minute == 23 and (msg.time.second == 45 or (msg.time.second == 46 and msg.time.microsecond < 330000)):
        getUser(msg.sender).playSuite()
      else:
        getUser(msg.sender).playBad()

    if re.match("^[1l][e3]{2}[t7] ?t?ime.{,2}$", msg.content.strip().lower()):
      if msg.time.hour == 13 and msg.time.minute == 37:
        if msg.time.second == 0:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playLeet()
      else:
        getUser(msg.sender).playBad()

    if re.match("^(pi|3.14) ?time.{,2}$", msg.content.strip().lower()):
      if msg.time.hour == 3 and msg.time.minute == 14:
        if msg.time.second == 15 or msg.time.second == 16:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playPi()
      else:
        getUser(msg.sender).playBad()

    if re.match("^(404( ?time)?|time ?not ?found).{,2}$", msg.content.strip().lower()):
      if msg.time.hour == 4 and msg.time.minute == 4:
        if msg.time.second == 0 or msg.time.second == 4:
          getUser(msg.sender).playGreat()
        getUser(msg.sender).playNotfound()
      else:
        getUser(msg.sender).playBad()

    if getUser(msg.sender).isWinner():
      print ("Nous avons un vainqueur ! Nouvelle manche :p")
      win(msg)
      return True
    elif getUser(msg.sender).hasChanged():
      gu = GameUpdater(msg, bfrseen)
      gu.start()
      return True
  return False

DELAYED = dict()

class DelayedTuple:
  def __init__(self, regexp, great):
    self.delayEvnt = threading.Event()
    self.msg = None
    self.regexp = regexp
    self.great = great

  def triche(self, res):
    if res is not None:
      return re.match(".*" + self.regexp + ".*", res.lower() + " ") is None
    else:
      return True

  def perfect(self, res):
    if res is not None:
      return re.match(".*" + self.great + ".*", res.lower() + " ") is not None
    else:
      return False

  def wait(self, timeout):
    self.delayEvnt.wait(timeout)

LASTQUESTION = 99999

class GameUpdater(threading.Thread):
  def __init__(self, msg, bfrseen):
    self.msg = msg
    self.bfrseen = bfrseen
    threading.Thread.__init__(self)

  def run(self):
    global DELAYED, LASTQUESTION

    if self.bfrseen is not None:
      seen = datetime.now() - self.bfrseen
      rnd = random.randint(0, int(seen.seconds/90))
    else:
      rnd = 1

    if rnd != 0:
      QUESTIONS = CONF.getNodes("question")

      if self.msg.channel == "#nemutest":
        quest = 9
      else:
        if LASTQUESTION >= len(QUESTIONS):
          random.shuffle(QUESTIONS)
          LASTQUESTION = 0
        quest = LASTQUESTION
        LASTQUESTION += 1

      question = QUESTIONS[quest]["question"]
      regexp = QUESTIONS[quest]["regexp"]
      great = QUESTIONS[quest]["great"]
      self.msg.send_chn("%s: %s" % (self.msg.sender, question))

      DELAYED[self.msg.sender] = DelayedTuple(regexp, great)

      DELAYED[self.msg.sender].wait(20)

      if DELAYED[self.msg.sender].triche(DELAYED[self.msg.sender].msg):
        getUser(self.msg.sender).playTriche()
        self.msg.send_chn("%s: Tricheur !" % self.msg.sender)
      elif DELAYED[self.msg.sender].perfect(DELAYED[self.msg.sender].msg):
        if random.randint(0, 10) == 1:
          getUser(self.msg.sender).bonusQuestion()
        self.msg.send_chn("%s: Correct !" % self.msg.sender)
      else:
        self.msg.send_chn("%s: J'accepte" % self.msg.sender)
      del DELAYED[self.msg.sender]
    SCORES.save(self.msg.sender)
    save()
