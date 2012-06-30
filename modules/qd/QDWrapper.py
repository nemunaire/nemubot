# coding=utf-8

from wrapper import Wrapper
from .Score import Score

class QDWrapper(Wrapper):
  def __init__(self, datas):
    Wrapper.__init__(self)
    self.DATAS = datas
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
