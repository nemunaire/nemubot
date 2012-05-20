# coding=utf-8

import re
import time
import random
import sys
import threading
from datetime import timedelta
from datetime import datetime
from datetime import date
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation

filename = ""
channels = "#nemutest #42sh #ykar #epitagueule"
MANCHE = None
QUESTIONS = list()
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
  def playTriche(self):
    self.changed = True
    self.bad += 5
  def oupsTriche(self):
    self.changed = True
    self.bad -= 5
  def bonusQuestion(self):
    self.changed = True

  def toTuple(self):
    return (self.ftt, self.twt, self.pi, self.notfound, self.tententen, self.leet, self.great, self.bad)

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
    return (self.ftt * 2 - self.bad * 10 + self.great * 5 + self.leet * 3 + self.pi * 3.1415 + self.twt + self.notfound * 4.04)

  def details(self):
    return "42: %d, 23: %d, bad: %d, great: %d, leet: %d, pi: %d, 404: %d, 10: %d = %d."%(self.ftt, self.twt, self.bad, self.great, self.leet, self.pi, self.notfound, self.tententen, self.score())


def xmlparse(node):
  """Parse the given node and add scores to the global list."""
  global SCORES, MANCHE
  for item in node.getElementsByTagName("score"):
    SCORES[item.getAttribute("name")] = Score ()
    SCORES[item.getAttribute("name")].parse(item)

  for item in node.getElementsByTagName("question"):
    QUESTIONS.append((item.getAttribute("question"),item.getAttribute("regexp"),item.getAttribute("great")))

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
  print ("done (%d loaded, %d questions, currently in round %d)" % (len(SCORES), len(QUESTIONS), -42))

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

  for q in QUESTIONS:
    top.appendChild(parseString ('<question question="%s" regexp="%s" great="%s" />' % q).documentElement)

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
              phrase = " *%s.%s: %d*,"%(nom[0:1], nom[1:len(nom)], score)
            else:
              phrase += " %s.%s: %d,"%(nom[0:1], nom[1:len(nom)], score)

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
  SCORES[who] = Score()
  SCORES[who].newWinner()

  if who != maxi_name:
    msg.send_chn ("Félicitations %s, tu remportes cette manche terminée par %s, avec un score de %d !"%(maxi_name, who, maxi_scor))
  else:
    msg.send_chn ("Félicitations %s, tu remportes cette manche avec %d points !"%(maxi_name, maxi_scor))

  MANCHE = (num_manche + 1, maxi_name, maxi_scor, who, datetime.now ())

  print ("Nouvelle manche :", MANCHE)
  save_module ()


def parseask (msg):
  if len(DELAYED) > 0:
    if msg.sender in DELAYED:
      DELAYED[msg.sender].msg = msg.content[9:]
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

    if re.match("^[1l][e3]{2}[t7] ?time.{,2}$", msg.content.strip().lower()):
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
      gu = GameUpdater(msg)
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

#<question question=" ?" regexp="microprocesseur"/>
#<question question=" ?" regexp=""/>

  def wait(self, timeout):
    self.delayEvnt.wait(timeout)

LASTQUESTION = 99999

class GameUpdater(threading.Thread):
  def __init__(self, msg):
    self.msg = msg
    threading.Thread.__init__(self)

  def run(self):
    global DELAYED, QUESTIONS, LASTQUESTION

    rnd = random.randint(0, 3)
    print (rnd)
    if rnd != 2:
      if self.msg.channel == "#nemutest":
        quest = 9
      else:
        if LASTQUESTION >= len(QUESTIONS):
          random.shuffle(QUESTIONS)
          LASTQUESTION = 0
        quest = LASTQUESTION
        LASTQUESTION += 1

      (question, regexp, great) = QUESTIONS[quest]
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
      del DELAYED[self.msg.sender]
    save_module ()
