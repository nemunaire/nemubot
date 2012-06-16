# coding=utf-8

import http.client
import re
import sys
import threading

nemubotversion = 3.0

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Gets YCC urls"

def help_full ():
  return "TODO"


class Tinyfier(threading.Thread):
  def __init__(self, url, msg):
    self.url = url
    self.msg = msg
    threading.Thread.__init__(self)

  def run(self):
    (status, page) = getPage("ycc.fr", "/redirection/create/" + self.url)
    if status == http.client.OK:
      srv = re.match(".*((ht|f)tps?://|www.)([^/]+).*", self.url)
      if srv is None:
        self.msg.send_chn("Mauvaise URL : %s" % (self.url))
      else:
        self.msg.send_chn("URL pour %s : %s" % (srv.group(3), page.decode()))
    else:
      print ("ERROR: ycc.fr seem down?")

def parseanswer(msg):
  global LAST_URLS
  if msg.cmd[0] == "ycc":
    if len(msg.cmd) == 1:
      if msg.channel in LAST_URLS and len(LAST_URLS[msg.channel]) > 0:
        url = LAST_URLS[msg.channel].pop()
        t = Tinyfier(url, msg)
        t.start()
      else:
        msg.send_chn("%s: je n'ai pas d'autre URL a reduire" % msg.sender)
    else:
      if len(msg.cmd) < 6:
        for url in msg.cmd[1:]:
          t = Tinyfier(url, msg)
          t.start()
      else:
        msg.send_chn("%s: je ne peux pas reduire autant d'URL d'un seul coup." % msg.sender)
    return True
  else:
    return False

LAST_URLS = dict()

def parselisten (msg):
  global LAST_URLS
  if re.match(".*(https?://|www\.)[^ ]+.*", msg.content) is not None:
    res = re.match(".*(((ht|f)tps?://|www\.)[^ ]+).*", msg.content)
    if msg.channel in LAST_URLS:
      LAST_URLS[msg.channel].append(res.group(1))
    else:
      LAST_URLS[msg.channel] = list(res.group(1))
    return True
  return False

def getPage(s, p): 
  conn = http.client.HTTPConnection(s)
  try:
    conn.request("GET", p)
  except socket.gaierror:
    print ("[%s] impossible de récupérer la page %s."%(s, p))
    return None

  res = conn.getresponse()
  data = res.read()

  conn.close()
  return (res.status, data)
