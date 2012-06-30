# coding=utf-8

import threading

class Delayed:
  def __init__(self, name):
    self.name = name
    self.res = None
    self.evt = threading.Event()

  def wait(self, timeout):
    self.evt.clear()
    self.evt.wait(timeout)
