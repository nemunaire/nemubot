# coding=utf-8

import http.client
import threading
import re

class Tinyfier(threading.Thread):
  def __init__(self, url, msg):
    self.url = url
    self.msg = msg
    threading.Thread.__init__(self)

  def run(self):
    (status, page) = getPage("ycc.fr", "/redirection/create/" + self.url)
    if status == http.client.OK and len(page) < 100:
      srv = re.match(".*((ht|f)tps?://|www.)([^/ ]+).*", self.url)
      if srv is None:
        self.msg.send_chn("Mauvaise URL : %s" % (self.url))
      else:
        self.msg.send_chn("URL pour %s : %s" % (srv.group(3), page.decode()))
    else:
      print ("ERROR: ycc.fr seem down?")
      self.msg.send_chn("La situation est embarassante, il semblerait que YCC soit down :(")

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
