# coding=utf-8

import http.client
import re
from urllib.parse import quote

import xmlparser

class Wikipedia:
    def __init__(self, terms, lang="fr"):
        self.terms = terms
        self.lang = lang
        self.curRT = 0
        (res, page) = getPage(terms, self.lang)
        if res == http.client.OK or res == http.client.SEE_OTHER:
            self.wres = xmlparser.parse_string(page)
            if self.wres is None or not (self.wres.hasNode("query") and self.wres.getFirstNode("query").hasNode("pages") and self.wres.getFirstNode("query").getFirstNode("pages").hasNode("page") and self.wres.getFirstNode("query").getFirstNode("pages").getFirstNode("page").hasNode("revisions")):
                self.wres = None
            else:
                self.infobox = parseInfobox(self)
        else:
            self.wres = None

    @property
    def nextRes(self):
        if self.wres is not None:
            for cnt in self.wres.getFirstNode("query").getFirstNode("pages").getFirstNode("page").getFirstNode("revisions").getFirstNode("rev").getContent().split("\n"):
                if self.curRT > 0:
                    self.curRT -= 1
                    continue

                c = striplink(cnt).strip()
                if c != "":
                    yield c


def parseInfobox(w):
    inInfobox = False
    view=-1
    for cnt in w.wres.getFirstNode("query").getFirstNode("pages").getFirstNode("page").getFirstNode("revisions").getFirstNode("rev").getContent().split("\n"):
        view += 1
        if inInfobox:
            if cnt.find("}}") == 0:
                inInfobox=False
        elif cnt.find("{{") == 0:
            inInfobox=True
        else:
            w.curRT += view
            break

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

def getPage(terms, lang, site="wikipedia"):
    conn = http.client.HTTPConnection(lang + "." + site + ".org", timeout=5)
    try:
        conn.request("GET", "/w/api.php?format=xml&redirects&action=query&prop=revisions&rvprop=content&rvsection=0&titles=%s" % quote(terms), None, {"User-agent": "Nemubot v3"})
    except socket.gaierror:
        print ("impossible de récupérer la page %s."%(p))
        return (http.client.INTERNAL_SERVER_ERROR, None)

    res = conn.getresponse()
    data = res.read()

    conn.close()
    return (res.status, data)
