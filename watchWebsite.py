# coding=utf-8

import http.client
import hashlib
import time
import _thread
from urllib.parse import unquote
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation

import atom

filename = ""
SITES = []
SRVS = None

def xmlparse(node):
  """Parse the given node and add events to the global list."""
  for item in node.getElementsByTagName("watch"):
      if item.getAttribute("type"):
          type = item.getAttribute("type")
      else:
          type = "hash"

      SITES.append ((item.getAttribute("server"), item.getAttribute("page"), type, item.getAttribute("message"), None, 40))


def load_module(datas_path):
  """Load this module"""
  global SITES, filename
  SITES = []
  filename = datas_path + "/watch.xml"

  print ("Loading watchsites ...",)
  dom = parse(filename)
  xmlparse (dom.documentElement)
  print ("done (%d loaded)" % len(SITES))


def launch (servers):
    global SRVS
    SRVS = servers
    for site in SITES:
        _thread.start_new_thread (startThread, (site,))

def send_global (msg):
    for server in SRVS:
        server.send_global (msg)

def treat_atom (lastpage, content, message):
    change=False
    f = atom.Atom (content)
    if lastpage is not None:
        diff = lastpage.diff (f)
        if len(diff) > 0:
            if f.id == "http://public.nbr23.com/rss.php":
                for d in diff:
                    if d.summary == "Music":
                        messageI = message % ("quelles sont ces nouvelles musiques", "%s")
                    elif d.summary == "TV_Shows":
                        messageI = message % ("quelle est cette nouvelle série", "%s")
                    elif d.summary == "Movies":
                        messageI = message % ("quel est ce nouveau film", "%s")
                    elif d.summary == "Books":
                        messageI = message % ("quel est ce nouveau livre", "%s")
                    else:
                        messageI = message % ("quel est ce nouveau fichier", "%s")
                    send_global (messageI % unquote (d.link))
            elif message.find ("%s") >= 0:
                for d in diff:
                    send_global (message % unquote (d.link))
            else:
                send_global (message)
            change=True
    return (f,change)

def getPage (s, p):
    conn = http.client.HTTPConnection(s)
    conn.request("GET", "/%s"%(p))

    res = conn.getresponse()
    data = res.read()

    conn.close()
    return data

def startThread(site):
    (srv, page, type, message, lastpage, updateTime) = site

    lastChange = 0

    while 1:
        content = getPage(srv, page)

        if type == "atom":
            (lastpage, change) = treat_atom (lastpage, content, message)
            if change:
                if lastChange <= 0:
                    lastChange -= 1
                else:
                    lastChange = 0
            else:
                lastChange += 1
        else:
            hash = hashlib.sha224(content).hexdigest()
            if hash != lastpage:
                if lastpage is not None:
                    send_global (message)
                lastpage = hash
                if lastChange <= 0:
                    lastChange -= 1
                else:
                    lastChange = 0
            else:
                lastChange += 1

        #Update check time intervalle
        if lastChange >= 1 and updateTime < 60:
            updateTime *= 2
        elif lastChange >= 10 and updateTime < 200:
            updateTime *= 1.25
        elif lastChange >= 50 and updateTime < 500:
            updateTime *= 1.1
        elif lastChange < 0 and updateTime < 60:
            updateTime /= 2
        elif lastChange <= 0 and updateTime < 200:
            updateTime /= 3
        elif lastChange <= 0 and updateTime > 350:
            updateTime /= 7
        elif lastChange <= 0:
            updateTime /= 4.5

        if updateTime < 10:
            updateTime = 10
        if updateTime > 500:
            updateTime = 500

        time.sleep(updateTime)
