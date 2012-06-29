# coding=utf-8

nemubotversion = 3.0

from .Watcher import Watcher
from .Site import Site

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Alert on changes on websites"

def help_full ():
  return "This module is autonomous you can't interract with it."


WATCHER = None


def load():
  global WATCHER, DATAS
  #Load the watcher
  WATCHER = Watcher()
  for site in DATAS.getNodes("watch"):
    s = Site(site)
    WATCHER.addServer(s)
  WATCHER.start()

def close():
  global WATCHER
  if WATCHER is not None:
    WATCHER.stop = True
    WATCHER.newSrv.set()
