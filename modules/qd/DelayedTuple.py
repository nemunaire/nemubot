# coding=utf-8

import re
import threading

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

  def good(self, res):
    if res is not None:
      return re.match(".*" + self.regexp + ".*", res.lower() + " ") is not None
    else:
      return False

  def wait(self, timeout):
    self.delayEvnt.wait(timeout)
