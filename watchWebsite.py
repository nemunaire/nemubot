# coding=utf-8

import http.client
import hashlib
import sys
import time
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


  def start (self):
    self.thread = _thread.start_new_thread (startThread, (self,))

  def send_message (self, msg):
    global SRVS
    if len(self.channels) > 0:
      for server in SRVS:
        for chan in self.channels:
          server.send_msg (chan, msg)
    else:
      for server in SRVS:
        server.send_global (msg)

  def treat_atom (self, content):
    change=False
    f = atom.Atom (content)
    if self.lastpage is not None:
      diff = self.lastpage.diff (f)
      if len(diff) > 0:
        print ("[%s] Page differ!"%self.server)
        if f.id == "http://public.nbr23.com/rss.php":
          for d in diff:
            if d.category == None:
              messageI = self.message % ("quel est ce nouveau fichier", "%s")
            elif d.category == "Music":
              messageI = self.message % ("quelles sont ces nouvelles musiques", "%s")
            elif d.category == "TV_Shows":
              messageI = self.message % ("quelle est cette nouvelle série", "%s")
            elif d.category == "Movies":
              messageI = self.message % ("quel est ce nouveau film", "%s")
            elif d.category == "Books":
              messageI = self.message % ("quel est ce nouveau livre", "%s")
            else:
              messageI = self.message % ("quel est ce nouveau fichier", "%s")
            self.send_message (messageI % unquote (d.link))
        elif f.id == "http://musik.p0m.fr/atom.php?nemubot":
          for d in diff:
            youtube.send_global (d.link2, self.message % (d.title, unquote (d.link)))
        elif self.message.find ("%s") >= 0:
          print ("[%s] Send message!"%self.server)
          for d in diff:
            self.send_message (self.message % unquote (d.title))
        else:
          self.send_message (self.message)
        change=True
    return (f, change)

  def check (self):
    while self.run:
      try:
#        print ("Check %s/%s"%(self.server, self.page))
        content = getPage(self.server, self.page)

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
              self.send_message ()
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
    top.appendChild(item);

  with open(filename, "w") as f:
    newdoc.writexml (f)
  print ("done")


def help_tiny ():
  """Line inserted in the response to the command !help"""
  return None

def help_full ():
  return None

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
  conn.request("GET", "/%s"%(p))

  res = conn.getresponse()
  data = res.read()

  conn.close()
  return data

def startThread(site):
  site.check ()
