# coding=utf-8

from datetime import datetime

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
    now = datetime.now()
    ret = self.last == None or self.last.minute != now.minute or self.last.hour != now.hour or self.last.day != now.day
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
