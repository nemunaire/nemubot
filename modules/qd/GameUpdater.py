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
          print (QUESTIONS)
          random.shuffle(QUESTIONS)
          LASTQUESTION = 0
        quest = LASTQUESTION
        LASTQUESTION += 1

      question = QUESTIONS[quest]["question"]
      regexp = QUESTIONS[quest]["regexp"]
      great = QUESTIONS[quest]["great"]
      self.msg.send_chn("%s: %s" % (self.msg.nick, question))

      DELAYED[self.msg.nick] = DelayedTuple(regexp, great)

      DELAYED[self.msg.nick].wait(20)

      if DELAYED[self.msg.nick].triche(DELAYED[self.msg.nick].msg):
        getUser(self.msg.nick).playTriche()
        self.msg.send_chn("%s: Tricheur !" % self.msg.nick)
      elif DELAYED[self.msg.nick].perfect(DELAYED[self.msg.nick].msg):
        if random.randint(0, 10) == 1:
          getUser(self.msg.nick).bonusQuestion()
        self.msg.send_chn("%s: Correct !" % self.msg.nick)
      else:
        self.msg.send_chn("%s: J'accepte" % self.msg.nick)
      del DELAYED[self.msg.nick]
    SCORES.save(self.msg.nick)
    save()
