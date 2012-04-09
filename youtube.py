# coding=utf-8

import re
import http.client

URLS = dict ()

def load_module(datas_path):
  """Load this module"""
  global URLS
  URLS = dict ()

def save_module():
  """Save the dates"""
  return

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return

def help_full ():
  return

def parseanswer(msg):
  return False


def parseask(msg):
  return False

def parselisten (msg):
  global URLS
  matches = [".*(http://(www\.)?youtube.com/watch\?v=([a-zA-Z0-9_-]{11})).*",
             ".*(http://(www\.)?youtu.be/([a-zA-Z0-9_-]{11})).*"]
  for m in matches:
    res = re.match (m, msg.content)
    if res is not None:
      #print ("seen : %s"%res.group(1))
      URLS[res.group(1)] = msg
      conn = http.client.HTTPConnection("musik.p0m.fr")
      conn.request("GET", "/?nemubot&a=add&url=%s"%(res.group (1)))
      conn.getresponse()
      conn.close()
      return True
  return False

def send_global (origin, msg):
  if origin in URLS:
    URLS[origin].send_chn (msg)
    del URLS[origin]
