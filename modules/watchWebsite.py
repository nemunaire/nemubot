# coding=utf-8

from datetime import timedelta
from datetime import datetime
from datetime import date
import http.client
import hashlib
import sys
import traceback
import socket
import time
import base64
import threading
from urllib.parse import unquote

from module_state import ModuleState

nemubotversion = 3.0

import atom

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


class Watcher(threading.Thread):
  def __init__(self):
    self.servers = list()
    self.stop = False
    self.newSrv = threading.Event()
    threading.Thread.__init__(self)

  def addServer(self, server):
    self.servers.append(server)
    self.newSrv.set()

  def check(self, closer):
    closer.check()
    self.newSrv.set()

  def run(self):
    while not self.stop:
      self.newSrv.clear()
      closer = None
      #Gets the closer server update
      for server in self.servers:
        if server.update < datetime.now():
          #print ("Closer now: %s à %s"%(server.url, server.update))
          self.check(server)
        elif closer is None or server.update < closer.update:
          closer = server
      if closer is not None:
        #print ("Closer: %s à %s"%(closer.url, closer.update))
        timeleft = (closer.update - datetime.now()).seconds
        timer = threading.Timer(timeleft, self.check, (closer,))
        timer.start()
        #print ("Start timer (%ds)"%timeleft)

      self.newSrv.wait()

      if closer is not None and closer.update is not None and closer.update > datetime.now():
        timer.cancel()

  def stop(self):
    self.stop = True
    self.newSrv.set()


class Site:
  def __init__(self, item):
    self.server = item.getAttribute("server")
    self.page = item.getAttribute("page")
    if len(self.page) <= 0 or self.page[0] != "/":
      self.page = "/" + self.page
    if item.hasAttribute("type"):
      self.type = item.getAttribute("type")
    else:
      self.type = "hash"
    self.message = item.getAttribute("message")

    if item.hasAttribute("time"):
      self.updateTime = item.getInt("time")
    else:
      self.updateTime = 60
    self.lastChange = datetime.now()
    self.lastpage = None

    self.channels = list()
    for channel in item.getNodes('channel'):
      self.channels.append(channel.getAttribute("name"))

    self.categories = dict()
    for category in item.getNodes('category'):
      self.categories[category.getAttribute("term")] = category.getAttribute("part")

  @property
  def update(self):
    if self.lastpage is None:
      return self.lastChange
    else:
      return self.lastChange + timedelta(seconds=self.updateTime)

  @property
  def url(self):
    return self.server + self.page

  def send_message (self, msg):
    global SRVS
    if len(self.channels) > 0:
      for server in SRVS.keys():
        for chan in self.channels:
          SRVS[server].send_msg (chan, msg)
    else:
      for server in SRVS.keys():
        SRVS[server].send_global (msg)

  def treat_atom (self, content):
    change=False
    f = atom.Atom (content)
    if self.lastpage is not None:
      diff = self.lastpage.diff (f)
      if len(diff) > 0:
        print ("[%s] Page differ!"%self.server)
        diff.reverse()
        for d in diff:
          if self.message.count("%s") == 2 and len(self.categories) > 0:
            if d.category is None or d.category not in self.categories:
              messageI = self.message % (self.categories[""], "%s")
            else:
              messageI = self.message % (self.categories[d.category], "%s")
            self.send_message (messageI % unquote (d.link))
          elif self.message.count("%s") == 2:
            if f.id == youtube.idAtom:
              youtube.send_global (d.link2, self.message % (d.title, unquote (d.link)))
            else:
              self.send_message (self.message % (d.title, unquote (d.link)))
          elif self.message.count("%s") == 1:
            self.send_message(self.message % unquote (d.title))
          else:
            self.send_message(self.message)
        change=True
    return (f, change)

  def check (self):
    try:
      #print ("Check %s"%(self.url))
      (status, content) = getPage(self.server, self.page)
      if content is None:
        return

      if self.type == "atom":
        (self.lastpage, change) = self.treat_atom (content)
      else:
        hash = hashlib.sha224(content).hexdigest()
        if hash != self.lastpage:
          if self.lastpage is not None:
            self.send_message (self.message)
          self.lastpage = hash

      self.lastChange = datetime.now()

#      if self.updateTime < 10:
#        self.updateTime = 10
#      if self.updateTime > 400:
#        self.updateTime = 400
    except:
      print ("Une erreur est survenue lors de la récupération de la page " + self.server + "/" + self.page)
      exc_type, exc_value, exc_traceback = sys.exc_info()
      traceback.print_exception(exc_type, exc_value, exc_traceback)
      self.updateTime *= 2


def getPage(s, p): 
  conn = http.client.HTTPConnection(s)
  try:
    conn.request("GET", p)

    res = conn.getresponse()
    data = res.read()
  except socket.gaierror:
    print ("[%s] impossible de récupérer la page %s."%(s, p))
    return (None, None)

  conn.close()
  return (res.status, data)
