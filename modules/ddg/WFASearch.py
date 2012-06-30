# coding=utf-8

import http.client
import re
import socket
from urllib.parse import quote

import module_states_file as xmlparser

class WFASearch:
  def __init__(self, terms):
    self.terms = terms
    self.curPod = 1
    self.curSubPod = 0
    (res, page) = getPage(terms)
    if res == http.client.OK:
      self.wfares = xmlparser.parse_string(page)
    else:
      self.wfares = None

  @property
  def success(self):
    try:
      return self.wfares["success"] == "true"
    except:
      return False

  @property
  def error(self):
    return self.wfares["error"] == "true"

  @property
  def nextRes(self):
    try:
      if len(self.wfares.getNodes("pod")) > self.curPod:
        txt = ""
        while txt == "" or subnode.getFirstNode("plaintext").getContent().strip() == "":
          node = self.wfares.getNodes("pod")[self.curPod]
          subnode = node.getNodes("subpod")[self.curSubPod]

          self.curSubPod += 1
          if len(node.getNodes("subpod")) <= self.curSubPod:
            self.curPod += 1
            self.curSubPod = 0

          txt = node["title"] + ": " + subnode.getFirstNode("plaintext").getContent().strip()
        return txt
    except IndexError:
      pass
    self.curPod = 1
    return "No more results"


def getPage(terms):
  conn = http.client.HTTPConnection("api.wolframalpha.com")
  try:
    conn.request("GET", "/v2/query?input=%s&appid=%s" % (quote(terms), CONF.getNode("wfaapi")["key"]))
  except socket.gaierror:
    print ("impossible de récupérer la page Wolfram|Alpha.")
    return (http.client.INTERNAL_SERVER_ERROR, None)
  except (TypeError, KeyError):
    print ("You need a Wolfram|Alpha API key in order to use this module. Add it to the module configuration file:\n<wfaapi key=\"XXXXXX-XXXXXXXXXX\" />\nRegister at http://products.wolframalpha.com/api/")
    return (http.client.INTERNAL_SERVER_ERROR, None)

  res = conn.getresponse()
  data = res.read()

  conn.close()
  return (res.status, data)
