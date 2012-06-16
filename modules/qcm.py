# coding=utf-8

import re
import random
import sys

from module_state import ModuleState
import module_states_file as xmlparser

nemubotversion = 3.0

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "MCQ module"

def help_full ():
  return "todo"

class QuestionFile:
  def __init__(self, filename):
    self.questions = xmlparser.parse_file(filename)
    self.questions.setIndex("xml:id")

  def getQuestion(self, ident):
    if ident in self.questions.index:
      return Question(self.questions.index[ident])
    else:
      return None

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
    return self.node["course"]

  @property
  def answers(self):
    return self.node.getNodes("answer")

  @property
  def validator(self):
    return self.node["validator"]

  @property
  def validated(self):
    return self.node["validated"]

  @property
  def addedtime(self):
    return datetime.fromtimestamp(time.mktime(self.node["addedtime"]))

  @property
  def author(self):
    return "N/A"

  @property
  def tupleInfo(self):
    return (self.author, self.validator, self.addedtime)

  @property
  def bestAnswer(self):
    best = self.answers[0]
    for answer in self.answers:
      if best.getInt("score") < answer.getInt("score"):
        best = answer
    return best["answer"]

  def isCorrect(self, msg):
    for answer in self.answers:
      if msg == answer["answer"]:
        return True
    return False

  def getScore(self, msg):
    for answer in self.answers:
      if msg.lower() == answer["answer"].lower():
        return answer.getInt("score")
    return 0

class Session:
  def __init__(self):
    self.questions = list()
    self.current = -1
    self.score = 0
    self.good = 0
    self.bad = 0
    self.trys = 0

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

QUESTIONS = None
SESSIONS = dict()

def buildSession(user, categ = None, nbQuest = 5):
  global QUESTIONS
  if QUESTIONS is None:
    QUESTIONS = xmlparser.parse_file(CONF.getNode("file")["url"])
    QUESTIONS.setIndex("xml:id")
    #Remove no validated questions
    keys = list()
    for k in QUESTIONS.index.keys():
      keys.append(k)
    for ques in keys:
      if QUESTIONS.index[ques]["validated"] != "1":
        del QUESTIONS.index[ques]

  nbQuest = min(nbQuest, len(QUESTIONS.index))

  sess = Session()
  maxQuest = len(QUESTIONS.childs) - 1
  for i in range(0, nbQuest):
    while True:
      q = QUESTIONS.childs[random.randint(0, maxQuest)]
      if q["xml:id"] is not None and q["validated"] == "1" and sess.addQuestion(q["xml:id"]):
        break
  SESSIONS[user] = sess


def askQuestion(msg, bfr = ""):
  nextQ = SESSIONS[msg.sender].next_question()
  if nextQ is not None:
    msg.send_chn("%s: %s%s" % (msg.sender, bfr, nextQ.question))
  else:
    sess = SESSIONS[msg.sender]
    if sess.good > 1:
      goodS = "s"
    else:
      goodS = ""
    msg.send_chn("%s: %sFini, tu as donné %d bonne%s réponse%s sur %d questions." % (msg.sender, bfr, sess.good, goodS, goodS, len(sess.questions)))
    del SESSIONS[msg.sender]


def parseanswer(msg):
  global DATAS
  if msg.cmd[0] == "qcm":
    if msg.sender in SESSIONS:
      msg.send_chn("%s: tu as déjà une session de QCM en cours, finis-la avant d'en commencer une nouvelle." % msg.sender)
    else:
      buildSession(msg.sender)
      askQuestion(msg)
    return True
  elif msg.sender in SESSIONS:
    if msg.cmd[0] == "info" or msg.cmd[0] == "infoquestion":
      msg.send_chn("Cette question a été écrite par %s et validée par %s, le %s" % SESSIONS[msg.sender].question.tupleInfo)
    elif msg.cmd[0] == "report" or msg.cmd[0] == "reportquestion":
      msg.send_chn("%s: fonction non implémentée" % msg.sender)
    return True
  return False

def parseask(msg):
  if msg.sender in SESSIONS:
    if SESSIONS[msg.sender].question.isCorrect(msg.content):
      SESSIONS[msg.sender].good += 1
      SESSIONS[msg.sender].score += SESSIONS[msg.sender].question.getScore(msg.content)
      askQuestion(msg, "correct ; ")
    else:
      SESSIONS[msg.sender].bad += 1
      if SESSIONS[msg.sender].trys == 0:
        SESSIONS[msg.sender].trys = 1
        msg.send_chn("%s: non, essaie encore :p" % msg.sender)
      else:
        askQuestion(msg, "non, la bonne reponse était : %s ; " % SESSIONS[msg.sender].question.bestAnswer)
    return True
  return False
