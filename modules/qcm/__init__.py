# coding=utf-8

from datetime import datetime
import http.client
import re
import random
import sys
import time

nemubotversion = 3.0

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "MCQ module, working with http://bot.nemunai.re/"

def help_full ():
  return "!qcm [<nbQuest>] [<theme>]"

from . import Question
from . import Course
from . import Session

def load():
  CONF.setIndex("name", "file")

def buildSession(msg, categ = None, nbQuest = 10, channel = False):
  if Question.QUESTIONS is None:
    Question.QUESTIONS = xmlparser.parse_file(CONF.index["main"]["url"])
    Question.QUESTIONS.setIndex("xml:id")
    Course.COURSES = xmlparser.parse_file(CONF.index["courses"]["url"])
    Course.COURSES.setIndex("xml:id")
    User.USERS = xmlparser.parse_file(CONF.index["users"]["url"])
    User.USERS.setIndex("xml:id")
    #Remove no validated questions
    keys = list()
    for k in Question.QUESTIONS.index.keys():
      keys.append(k)
    for ques in keys:
      if Question.QUESTIONS.index[ques]["validated"] != "1" or Question.QUESTIONS.index[ques]["reported"] == "1":
        del Question.QUESTIONS.index[ques]

  #Apply filter
  QS = list()
  if categ is not None and len(categ) > 0:
    #Find course id corresponding to categ
    courses = list()
    for c in Course.COURSES.childs:
      if c["code"] in categ:
        courses.append(c["xml:id"])

    #Keep only questions matching course or branch
    for q in Question.QUESTIONS.index.keys():
      if (Question.QUESTIONS.index[q]["branch"] is not None and Question.QUESTIONS.index[q]["branch"].find(categ)) or Question.QUESTIONS.index[q]["course"] in courses:
        QS.append(q)
  else:
    for q in Question.QUESTIONS.index.keys():
      QS.append(q)

  nbQuest = min(nbQuest, len(QS))

  if channel:
    sess = Session.Session(msg.srv, msg.channel, msg.channel)
  else:
    sess = Session.Session(msg.srv, msg.channel, msg.sender)
  maxQuest = len(QS) - 1
  for i in range(0, nbQuest):
    while True:
      q = QS[random.randint(0, maxQuest)]
      if sess.addQuestion(q):
        break
  if channel:
    Session.SESSIONS[msg.channel] = sess
  else:
    Session.SESSIONS[msg.sender] = sess


def askQuestion(msg, bfr = ""):
  Session.SESSIONS[msg.sender].askNext(bfr)

def parseanswer(msg):
  global DATAS
  if msg.cmd[0] == "qcm" or msg.cmd[0] == "qcmchan" or msg.cmd[0] == "simulateqcm":
    if msg.sender in Session.SESSIONS:
      if len(msg.cmd) > 1:
        if msg.cmd[1] == "stop" or msg.cmd[1] == "end":
          sess = Session.SESSIONS[msg.sender]
          if sess.good > 1: goodS = "s"
          else: goodS = ""
          msg.send_chn("%s: Fini, tu as donné %d bonne%s réponse%s sur %d questions." % (msg.sender, sess.good, goodS, goodS, sess.current))
          del Session.SESSIONS[msg.sender]
          return True
        elif msg.cmd[1] == "next" or msg.cmd[1] == "suivant" or msg.cmd[1] == "suivante":
          askQuestion(msg)
          return True
      msg.send_chn("%s: tu as déjà une session de QCM en cours, finis-la avant d'en commencer une nouvelle." % msg.sender)
    elif msg.channel in Session.SESSIONS:
      if len(msg.cmd) > 1:
        if msg.cmd[1] == "stop" or msg.cmd[1] == "end":
          sess = Session.SESSIONS[msg.channel]
          if sess.good > 1: goodS = "s"
          else: goodS = ""
          msg.send_chn("Fini, vous avez donné %d bonne%s réponse%s sur %d questions." % (sess.good, goodS, goodS, sess.current))
          del Session.SESSIONS[msg.channel]
          return True
        elif msg.cmd[1] == "next" or msg.cmd[1] == "suivant" or msg.cmd[1] == "suivante":
          Session.SESSIONS[msg.channel].prepareNext(1)
          return True
    else:
      nbQuest = 10
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
      if msg.channel in Session.SESSIONS:
        msg.send_snd("Il y a deja une session de QCM sur ce chan.")
      else:
        buildSession(msg, filtre, nbQuest, msg.cmd[0] == "qcmchan")
        if msg.cmd[0] == "qcm":
          askQuestion(msg)
        elif msg.cmd[0] == "qcmchan":
          Session.SESSIONS[msg.channel].askNext()
        else:
          msg.send_chn("QCM de %d questions" % len(Session.SESSIONS[msg.sender].questions))
          del Session.SESSIONS[msg.sender]
    return True
  elif msg.sender in Session.SESSIONS:
    if msg.cmd[0] == "info" or msg.cmd[0] == "infoquestion":
      msg.send_chn("Cette question a été écrite par %s et validée par %s, le %s" % Session.SESSIONS[msg.sender].question.tupleInfo)
      return True
    elif msg.cmd[0] == "report" or msg.cmd[0] == "reportquestion":
      if len(msg.cmd) == 1:
        msg.send_chn("Veuillez indiquer une raison de report")
      elif Session.SESSIONS[msg.sender].question.report(' '.join(msg.cmd[1:])):
        msg.send_chn("Cette question vient d'être signalée.")
        Session.SESSIONS[msg.sender].askNext()
      else:
        msg.send_chn("Une erreur s'est produite lors du signalement de la question, veuillez recommencer plus tard.")
      return True
  elif msg.channel in Session.SESSIONS:
    if msg.cmd[0] == "info" or msg.cmd[0] == "infoquestion":
      msg.send_chn("Cette question a été écrite par %s et validée par %s, le %s" % Session.SESSIONS[msg.channel].question.tupleInfo)
      return True
    elif msg.cmd[0] == "report" or msg.cmd[0] == "reportquestion":
      if len(msg.cmd) == 1:
        msg.send_chn("Veuillez indiquer une raison de report")
      elif Session.SESSIONS[msg.channel].question.report(' '.join(msg.cmd[1:])):
        msg.send_chn("Cette question vient d'être signalée.")
        Session.SESSIONS[msg.channel].prepareNext()
      else:
        msg.send_chn("Une erreur s'est produite lors du signalement de la question, veuillez recommencer plus tard.")
      return True
  else:
    if msg.cmd[0] == "listecours":
      if Course.COURSES is None:
        msg.send_chn("La liste de cours n'est pas encore construite, lancez un QCM pour la construire.")
      else:
        lst = ""
        for cours in Course.COURSES.getNodes("course"):
          lst += cours["code"] + " (" + cours["name"] + "), "
        msg.send_chn("Liste des cours existants : " + lst[:len(lst)-2])
    elif msg.cmd[0] == "refreshqcm":
      Question.QUESTIONS = None
      Course.COURSES = None
      User.USERS = None
  return False

def parseask(msg):
  if msg.sender in Session.SESSIONS:
    dest = msg.sender

    if Session.SESSIONS[dest].question.isCorrect(msg.content):
      Session.SESSIONS[dest].good += 1
      Session.SESSIONS[dest].score += Session.SESSIONS[dest].question.getScore(msg.content)
      askQuestion(msg, "correct ; ")
    else:
      Session.SESSIONS[dest].bad += 1
      if Session.SESSIONS[dest].trys == 0:
        Session.SESSIONS[dest].trys = 1
        msg.send_chn("%s: non, essaie encore :p" % msg.sender)
      else:
        askQuestion(msg, "non, la bonne reponse était : %s ; " % Session.SESSIONS[dest].question.bestAnswer)
    return True

  elif msg.channel in Session.SESSIONS:
    dest = msg.channel

    if Session.SESSIONS[dest].question.isCorrect(msg.content):
      Session.SESSIONS[dest].good += 1
      Session.SESSIONS[dest].score += Session.SESSIONS[dest].question.getScore(msg.content)
      msg.send_chn("%s: correct :)" % msg.sender)
      Session.SESSIONS[dest].prepareNext()
    else:
      Session.SESSIONS[dest].bad += 1
      msg.send_chn("%s: non, essaie encore :p" % msg.sender)
    return True
  return False
