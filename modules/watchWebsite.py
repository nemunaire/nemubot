# coding=utf-8

import http.client
import hashlib
import sys
import traceback
import socket
import time
import base64
import _thread
from urllib.parse import unquote
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation

import atom
import youtube

filename = ""
SITES = []
SRVS = None

class Site:
  def __init__(self, item):
    self.server = item.getAttribute("server")
    self.page = item.getAttribute("page")
    if item.getAttribute("type"):
      self.type = item.getAttribute("type")
    else:
      self.type = "hash"
    self.message = item.getAttribute("message")

    self.thread = None
    if item.getAttribute("time"):
      self.updateTime = int(item.getAttribute("time"))
    else:
      self.updateTime = 60
    self.lastChange = 0
    self.lastpage = None

    self.run = True

    self.channels = list()
    for channel in item.getElementsByTagName('channel'):
      self.channels.append(channel.getAttribute("name"))

    self.categories = dict()
    for category in item.getElementsByTagName('category'):
      self.categories[category.getAttribute("term")] = category.getAttribute("part")


  def start (self):
    self.thread = _thread.start_new_thread (startThread, (self,))

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
    while self.run:
      try:
        #print ("Check %s/%s"%(self.server, self.page))
        content = getPage(self.server, self.page)
        if content is None:
          return

        if self.type == "atom":
          (self.lastpage, change) = self.treat_atom (content)
          if change:
            if self.lastChange <= 0:
              self.lastChange -= 1
            else:
              self.lastChange = 0
          else:
            self.lastChange += 1
        else:
          hash = hashlib.sha224(content).hexdigest()
          if hash != self.lastpage:
            if self.lastpage is not None:
              self.send_message (self.message)
            self.lastpage = hash
            if self.lastChange <= 0:
              self.lastChange -= 1
            else:
              self.lastChange = 0
          else:
            self.lastChange += 1

        #Update check time intervalle
          #TODO

        if self.updateTime < 10:
          self.updateTime = 10
        if self.updateTime > 400:
          self.updateTime = 400

        time.sleep(self.updateTime)
      except:
          print ("Une erreur est survenue lors de la récupération de la page " + self.server + "/" + self.page)
          exc_type, exc_value, exc_traceback = sys.exc_info()
          traceback.print_exception(exc_type, exc_value, exc_traceback)
          time.sleep(self.updateTime * 3)



def load_module(datas_path):
  """Load this module"""
  global SITES, filename
  SITES = []
  filename = datas_path + "/watch.xml"

  sys.stdout.write ("Loading watchsites ... ")
  dom = parse(filename)
  for item in dom.documentElement.getElementsByTagName("watch"):
      SITES.append (Site (item))
  print ("done (%d loaded)" % len(SITES))


def launch (servers):
    global SRVS
    SRVS = servers
    for site in SITES:
        site.start ()
def stop():
  return

def save_module():
  """Save the module state"""
  global filename
  sys.stdout.write ("Saving watched sites ... ")
  impl = getDOMImplementation()
  newdoc = impl.createDocument(None, 'service', None)
  top = newdoc.documentElement

  for site in SITES:
    item = parseString ('<watch server="%s" page="%s" message="%s" type="%s" time="%d" />' % (site.server, site.page, site.message, site.type, site.updateTime)).documentElement
    if len(site.channels) > 0:
      for chan in site.channels:
        item.appendChild(parseString ('<channel name="%s" />' % (chan)).documentElement);
    if len(site.categories) > 0:
      for categ in site.categories.keys():
        item.appendChild(parseString ('<category term="%s" part="%s"/>' % (categ, site.categories[categ])).documentElement);
    #print (site.server)
    top.appendChild(item);

  with open(filename, "w") as f:
    newdoc.writexml (f)
  print ("done")


def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Alert on changes on websites"

def help_full ():
  return "This module is autonomous you can't interract with it."

def parseanswer (msg):
  if msg.cmd[0] == "watch":
    print ("print states here")
    return True
  return False

def parseask (msg):
  return False

def parselisten (msg):
  return False


def getPage (s, p):
  conn = http.client.HTTPConnection(s)
  try:
    conn.request("GET", "/%s"%(p))
  except socket.gaierror:
    print ("[%s] impossible de récupérer la page %s."%(s, p))
    return None

  res = conn.getresponse()
  data = res.read()

  conn.close()
  return data

def startThread(site):
  site.check ()