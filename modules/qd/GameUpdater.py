# coding=utf-8

from datetime import datetime
import random
import threading
from .DelayedTuple import DelayedTuple

DELAYED = dict()

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
