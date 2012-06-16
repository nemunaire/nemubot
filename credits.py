# coding=utf-8

from datetime import datetime
from datetime import timedelta
import random

BANLIST = []

class Credits:
  def __init__ (self, name):
    self.name = name
    self.credits = 5
    self.randsec = timedelta(seconds=random.randint(0, 55))
    self.lastmessage = datetime.now() + self.randsec
    self.iask = True

  def ask(self):
    if self.name in BANLIST:
      return False

    now = datetime.now() + self.randsec
    if self.lastmessage.minute == now.minute and (self.lastmessage.second == now.second or self.lastmessage.second == now.second - 1):
      print("\033[1;36mAUTOBAN\033[0m %s: too low time between messages" % self.name)
      #BANLIST.append(self.name)
      self.credits -= self.credits / 2 #Une alternative
      return False

    self.iask = True
    return self.credits > 0 or self.lastmessage.minute != now.minute

  def speak(self):
    if self.iask:
      self.iask = False
      now = datetime.now() + self.randsec
      if self.lastmessage.minute != now.minute:
        self.credits = min (15, self.credits + 5)
      self.lastmessage = now

    self.credits -= 1
    return self.credits > -3

  def to_string(self):
    print ("%s: %d ; reset: %d" % (self.name, self.credits, self.randsec.seconds))
