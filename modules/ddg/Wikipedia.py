# coding=utf-8

import http.client
import re
from urllib.parse import quote

import module_states_file as xmlparser

class Wikipedia:
  def __init__(self, terms, lang="fr"):
    self.terms = terms
    self.lang = lang
    self.curRT = -1
    (res, page) = getPage(terms, self.lang)
    if res == http.client.OK or res == http.client.SEE_OTHER:
      self.wres = xmlparser.parse_string(page)
    else:
      self.wres = None

  @property
  def nextRes(self):
    if self.wres is not None and self.wres.hasNode("query"):
      if self.wres.getFirstNode("query").hasNode("pages"):
        if self.wres.getFirstNode("query").getFirstNode("pages").hasNode("page"):
          if self.wres.getFirstNode("query").getFirstNode("pages").getFirstNode("page").hasNode("revisions"):
            self.curRT += 1
            content = self.wres.getFirstNode("query").getFirstNode("pages").getFirstNode("page").getFirstNode("revisions").getFirstNode("rev").getContent().split("\n")
            while self.curRT < len(content) and striplink(content[self.curRT]).strip() == "":
              self.curRT += 1
            return striplink(content[self.curRT])
    return "No more results"


def striplink(data):
  p = re.compile(r'(<!--.*-->|\{\{.*\}\}|\[\[[^\]]+\|[^\]]+\|[^\]\|]+\]\])')
  q = re.compile(r'\[\[([^\]]+)\|([^\]]+)]]')
  r = re.compile(r'\[\[([^\]]+)\]\]')
  (s, n) = p.subn('', data)
  if s == "":
    return s
  (s, n) = q.subn(r"\1", s)
  if s == "":
    return s
  (s, n) = r.subn(r"\1", s)
  return s.replace("'''", "*")

def getPage(terms, lang):
  conn = http.client.HTTPConnection(lang + ".wikipedia.org")
  try:
    conn.request("GET", "/w/api.php?format=xml&redirects&action=query&prop=revisions&rvprop=content&rvsection=0&titles=%s" % quote(terms), None, {"User-agent": "Nemubot v3"})
  except socket.gaierror:
    print ("impossible de récupérer la page %s."%(p))
    return (http.client.INTERNAL_SERVER_ERROR, None)

  res = conn.getresponse()
  data = res.read()

  conn.close()
  return (res.status, data)
