# coding=utf-8

import threading

SESSIONS = dict()

from . import Question

from response import Response

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
      return Question.Question(Question.QUESTIONS.index[self.questions[self.current]])
    else:
      return None

  def askNext(self, bfr = ""):
    global SESSIONS
    self.timer = None
    nextQ = self.next_question()
    if nextQ is not None:
        if self.sender.split("!")[0] != self.channel:
            self.server.send_response(Response(self.sender, "%s%s" % (bfr, nextQ.question), self.channel, nick=self.sender.split("!")[0]))
        else:
            self.server.send_response(Response(self.sender, "%s%s" % (bfr, nextQ.question), self.channel))
    else:
      if self.good > 1:
        goodS = "s"
      else:
        goodS = ""

      if self.sender.split("!")[0] != self.channel:
          self.server.send_response(Response(self.sender, "%sFini, tu as donné %d bonne%s réponse%s sur %d questions." % (self.sender, bfr, self.good, goodS, goodS, len(self.questions)), self.channel, nick=self.sender.split("!")[0]))
      else:
          self.server.send_response(Response(self.sender, "%sFini, tu as donné %d bonne%s réponse%s sur %d questions." % (self.sender, bfr, self.good, goodS, goodS, len(self.questions)), self.channel))
      del SESSIONS[self.sender]

  def prepareNext(self, lag = 3):
    if self.timer is None:
      self.timer = threading.Timer(lag, self.askNext)
      self.timer.start()

