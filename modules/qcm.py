# coding=utf-8

from datetime import datetime
import http.client
import hashlib
import re
import random
import socket
import sys
import threading
import time

from module_state import ModuleState
import module_states_file as xmlparser

nemubotversion = 3.0

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "MCQ module, working with http://bot.nemunai.re/"

def help_full ():
  return "!qcm [/nbQuest/] [/theme/]"

class QuestionFile:
  def __init__(self, filename):
    self.questions = xmlparser.parse_file(filename)
    self.questions.setIndex("xml:id")

  def getQuestion(self, ident):
    if ident in self.questions.index:
      return Question(self.questions.index[ident])
    else:
      return None

class Course:
  def __init__(self, iden):
    global COURSES
    if iden in COURSES.index:
      self.node = COURSES.index[iden]
    else:
      self.node = { "code":"N/A", "name":"N/A", "branch":"N/A" }

  @property
  def id(self):
    return self.node["xml:id"]

  @property
  def code(self):
    return self.node["code"]

  @property
  def name(self):
    return self.node["name"]

  @property
  def branch(self):
    return self.node["branch"]

  @property
  def validated(self):
    return int(self.node["validated"]) > 0
      

class User:
  def __init__(self, iden):
    global USERS
    if iden in USERS.index:
      self.node = USERS.index[iden]
    else:
      self.node = { "username":"N/A", "email":"N/A" }

  @property
  def id(self):
    return self.node["xml:id"]

  @property
  def username(self):
    return self.node["username"]

  @property
  def email(self):
    return self.node["email"]

  @property
  def validated(self):
    return int(self.node["validated"]) > 0
      

class Question:
  def __init__(self, node):
    self.node = node

  @property
  def ident(self):
    return self.node["xml:id"]

  @property
  def id(self):
    return self.node["xml:id"]

  @property
  def question(self):
    return self.node["question"]

  @property
  def course(self):
    return Course(self.node["course"])

  @property
  def answers(self):
    return self.node.getNodes("answer")

  @property
  def validator(self):
    return User(self.node["validator"])

  @property
  def writer(self):
    return User(self.node["writer"])

  @property
  def validated(self):
    return self.node["validated"]

  @property
  def addedtime(self):
    return datetime.fromtimestamp(float(self.node["addedtime"]))

  @property
  def author(self):
    return User(self.node["writer"])

  def report(self):
    conn = http.client.HTTPConnection(CONF.getNode("server")["url"])
    try:
      conn.request("GET", "report.php?id=" + hashlib.md5(self.id.encode()).hexdigest())
    except socket.gaierror:
      print ("[%s] impossible de récupérer la page %s."%(s, p))
      return False
    res = conn.getresponse()
    conn.close()
    return (res.status == http.client.OK)

  @property
  def tupleInfo(self):
    return (self.author.username, self.validator.username, self.addedtime)

  @property
  def bestAnswer(self):
    best = self.answers[0]
    for answer in self.answers:
      if best.getInt("score") < answer.getInt("score"):
        best = answer
    return best["answer"]

  def isCorrect(self, msg):
    msg = msg.lower().replace(" ", "")
    for answer in self.answers:
      if msg == answer["answer"].lower().replace(" ", ""):
        return True
    return False

  def getScore(self, msg):
    msg = msg.lower().replace(" ", "")
    for answer in self.answers:
      if msg == answer["answer"].lower().replace(" ", ""):
        return answer.getInt("score")
    return 0

class Session:
  def __init__(self, srv, chan, sender):
    self.questions = list()
    self.current = -1
    self.score = 0
    self.good = 0
    self.bad = 0
    self.trys = 0
    self.timer = None
    self.server = srv
    self.channel = chan
    self.sender = sender

  def addQuestion(self, ident):
    if ident not in self.questions:
      self.questions.append(ident)
      return True
    return False

  def next_question(self):
    self.trys = 0
    self.current += 1
    return self.question

  @property
  def question(self):
    if self.current >= 0 and self.current < len(self.questions):
      global QUESTIONS
      return Question(QUESTIONS.index[self.questions[self.current]])
    else:
      return None

  def askNext(self, bfr = ""):
    global SESSIONS
    self.timer = None
    nextQ = self.next_question()
    if nextQ is not None:
      if self.sender != self.channel:
        self.server.send_msg(self.channel, "%s: %s%s" % (self.sender, bfr, nextQ.question))
      else:
        self.server.send_msg(self.channel, "%s%s" % (bfr, nextQ.question))
    else:
      if self.good > 1:
        goodS = "s"
      else:
        goodS = ""
      if self.sender != self.channel:
        self.server.send_msg(self.channel, "%s: %sFini, tu as donné %d bonne%s réponse%s sur %d questions." % (self.sender, bfr, self.good, goodS, goodS, len(self.questions)))
      else:
        self.server.send_msg(self.channel, "%sFini, vous avez donné %d bonne%s réponse%s sur %d questions." % (bfr, self.good, goodS, goodS, len(self.questions)))
      del SESSIONS[self.sender]

  def prepareNext(self, lag = 3):
    if self.timer is None:
      self.timer = threading.Timer(lag, self.askNext)
      self.timer.start()

QUESTIONS = None
COURSES = None
USERS = None
SESSIONS = dict()

def load():
  CONF.setIndex("name", "file")

def buildSession(msg, categ = None, nbQuest = 5, channel = False):
  global QUESTIONS, COURSES, USERS
  if QUESTIONS is None:
    QUESTIONS = xmlparser.parse_file(CONF.index["main"]["url"])
    QUESTIONS.setIndex("xml:id")
    COURSES = xmlparser.parse_file(CONF.index["courses"]["url"])
    COURSES.setIndex("xml:id")
    USERS = xmlparser.parse_file(CONF.index["users"]["url"])
    USERS.setIndex("xml:id")
    #Remove no validated questions
    keys = list()
    for k in QUESTIONS.index.keys():
      keys.append(k)
    for ques in keys:
      if QUESTIONS.index[ques]["validated"] != "1" or QUESTIONS.index[ques]["reported"] == "1":
        del QUESTIONS.index[ques]

  #Apply filter
  QS = list()
  if categ is not None and len(categ) > 0:
    #Find course id corresponding to categ
    courses = list()
    for c in COURSES.childs:
      if c["code"] in categ:
        courses.append(c["xml:id"])

    #Keep only questions matching course or branch
    for q in QUESTIONS.index.keys():
      if (QUESTIONS.index[q]["branch"] is not None and QUESTIONS.index[q]["branch"].find(categ)) or QUESTIONS.index[q]["course"] in courses:
        QS.append(q)
  else:
    for q in QUESTIONS.index.keys():
      QS.append(q)

  nbQuest = min(nbQuest, len(QS))

  if channel:
    sess = Session(msg.srv, msg.channel, msg.channel)
  else:
    sess = Session(msg.srv, msg.channel, msg.sender)
  maxQuest = len(QS) - 1
  for i in range(0, nbQuest):
    while True:
      q = QS[random.randint(0, maxQuest)]
      if sess.addQuestion(q):
        break
  if channel:
    SESSIONS[msg.channel] = sess
  else:
    SESSIONS[msg.sender] = sess


def askQuestion(msg, bfr = ""):
  SESSIONS[msg.sender].askNext(bfr)

def parseanswer(msg):
  global DATAS, SESSIONS
  if msg.cmd[0] == "qcm" or msg.cmd[0] == "qcmchan" or msg.cmd[0] == "simulateqcm":
    if msg.sender in SESSIONS:
      if len(msg.cmd) > 1:
        if msg.cmd[1] == "stop" or msg.cmd[1] == "end":
          sess = SESSIONS[msg.sender]
          if sess.good > 1: goodS = "s"
          else: goodS = ""
          msg.send_chn("%s: Fini, tu as donné %d bonne%s réponse%s sur %d questions." % (msg.sender, sess.good, goodS, goodS, sess.current))
          del SESSIONS[msg.sender]
          return True
        elif msg.cmd[1] == "next" or msg.cmd[1] == "suivant" or msg.cmd[1] == "suivante":
          askQuestion(msg)
          return True
      msg.send_chn("%s: tu as déjà une session de QCM en cours, finis-la avant d'en commencer une nouvelle." % msg.sender)
    elif msg.channel in SESSIONS:
      if len(msg.cmd) > 1:
        if msg.cmd[1] == "stop" or msg.cmd[1] == "end":
          sess = SESSIONS[msg.channel]
          if sess.good > 1: goodS = "s"
          else: goodS = ""
          msg.send_chn("Fini, vous avez donné %d bonne%s réponse%s sur %d questions." % (sess.good, goodS, goodS, sess.current))
          del SESSIONS[msg.channel]
          return True
        elif msg.cmd[1] == "next" or msg.cmd[1] == "suivant" or msg.cmd[1] == "suivante":
          SESSIONS[msg.channel].prepareNext(1)
          return True
    else:
      nbQuest = 5
      filtre = list()
      if len(msg.cmd) > 1:
        for cmd in msg.cmd[1:]:
          try:
            tmp = int(cmd)
            nbQuest = tmp
          except ValueError:
            filtre.append(cmd.upper())
      if len(filtre) == 0:
        filtre = None
      if msg.channel in SESSIONS:
        msg.send_snd("Il y a deja une session de QCM sur ce chan.")
      else:
        buildSession(msg, filtre, nbQuest, msg.cmd[0] == "qcmchan")
        if msg.cmd[0] == "qcm":
          askQuestion(msg)
        elif msg.cmd[0] == "qcmchan":
          SESSIONS[msg.channel].askNext()
        else:
          msg.send_chn("QCM de %d questions" % len(SESSIONS[msg.sender].questions))
          del SESSIONS[msg.sender]
    return True
  elif msg.sender in SESSIONS:
    if msg.cmd[0] == "info" or msg.cmd[0] == "infoquestion":
      msg.send_chn("Cette question a été écrite par %s et validée par %s, le %s" % SESSIONS[msg.sender].question.tupleInfo)
      return True
    elif msg.cmd[0] == "report" or msg.cmd[0] == "reportquestion":
      if SESSIONS[msg.sender].question.report():
        msg.send_chn("Cette question vient vient d'etre signalée.")
        askQuestion(msg)
      else:
        msg.send_chn("Une erreur s'est produite lors du signalement de la question, veuillez recommencer plus tard.")
      return True
  elif msg.channel in SESSIONS:
    if msg.cmd[0] == "info" or msg.cmd[0] == "infoquestion":
      msg.send_chn("Cette question a été écrite par %s et validée par %s, le %s" % SESSIONS[msg.channel].question.tupleInfo)
      return True
    elif msg.cmd[0] == "report" or msg.cmd[0] == "reportquestion":
      if SESSIONS[msg.channel].question.report():
        msg.send_chn("Cette question vient vient d'etre signalée.")
        askQuestion(msg)
      else:
        msg.send_chn("Une erreur s'est produite lors du signalement de la question, veuillez recommencer plus tard.")
      return True
  return False

def parseask(msg):
  if msg.sender in SESSIONS:
    dest = msg.sender

    if SESSIONS[dest].question.isCorrect(msg.content):
      SESSIONS[dest].good += 1
      SESSIONS[dest].score += SESSIONS[dest].question.getScore(msg.content)
      askQuestion(msg, "correct ; ")
    else:
      SESSIONS[dest].bad += 1
      if SESSIONS[dest].trys == 0:
        SESSIONS[dest].trys = 1
        msg.send_chn("%s: non, essaie encore :p" % msg.sender)
      else:
        askQuestion(msg, "non, la bonne reponse était : %s ; " % SESSIONS[dest].question.bestAnswer)
    return True

  elif msg.channel in SESSIONS:
    dest = msg.channel

    if SESSIONS[dest].question.isCorrect(msg.content):
      SESSIONS[dest].good += 1
      SESSIONS[dest].score += SESSIONS[dest].question.getScore(msg.content)
      msg.send_chn("%s: correct :)" % msg.sender)
      SESSIONS[dest].prepareNext()
    else:
      SESSIONS[dest].bad += 1
      msg.send_chn("%s: non, essaie encore :p" % msg.sender)
    return True
  return False
