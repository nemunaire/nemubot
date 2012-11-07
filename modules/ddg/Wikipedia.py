# coding=utf-8

import re
from urllib.parse import quote
import urllib.request

import xmlparser

class Wikipedia:
    def __init__(self, terms, lang="fr", site="wikipedia.org", section=0):
        self.terms = terms
        self.lang = lang
        self.curRT = 0

        raw = urllib.request.urlopen(urllib.request.Request("http://" + self.lang + "." + site + "/w/api.php?format=xml&redirects&action=query&prop=revisions&rvprop=content&titles=%s" % (quote(terms)), headers={"User-agent": "Nemubot v3"}))
        self.wres = xmlparser.parse_string(raw.read())
        if self.wres is None or not (self.wres.hasNode("query") and self.wres.getFirstNode("query").hasNode("pages") and self.wres.getFirstNode("query").getFirstNode("pages").hasNode("page") and self.wres.getFirstNode("query").getFirstNode("pages").getFirstNode("page").hasNode("revisions")):
            self.wres = None
        else:
            self.wres = self.wres.getFirstNode("query").getFirstNode("pages").getFirstNode("page").getFirstNode("revisions").getFirstNode("rev").getContent()
            self.wres = striplink(self.wres) 

    @property
    def nextRes(self):
        if self.wres is not None:
            for cnt in self.wres.split("\n"):
                if self.curRT > 0:
                    self.curRT -= 1
                    continue

                (c, u) = RGXP_s.subn(' ', cnt)
                c = c.strip()
                if c != "":
                    yield c

RGXP_p = re.compile(r"(<!--.*-->|<ref[^>]*/>|<ref[^>]*>[^>]*</ref>|<dfn[^>]*>[^>]*</dfn>|\{\{[^}]*\}\}|\[\[([^\[\]]*\[\[[^\]\[]*\]\])+[^\[\]]*\]\]|\{\{([^{}]*\{\{.*\}\}[^{}]*)+\}\}|\[\[[^\]|]+(\|[^\]\|]+)*\]\])|#\* ''" + "\n", re.I)
RGXP_l = re.compile(r'\{\{(nobr|lang\|[^|}]+)\|([^}]+)\}\}', re.I)
RGXP_m = re.compile(r'\{\{pron\|([^|}]+)\|[^}]+\}\}', re.I)
RGXP_t = re.compile("==+ *([^=]+) *=+=\n+([^\n])", re.I)
RGXP_q = re.compile(r'\[\[([^\[\]|]+)\|([^\]|]+)]]', re.I)
RGXP_r = re.compile(r'\[\[([^\[\]|]+)\]\]', re.I)
RGXP_s = re.compile(r'\s+')

def striplink(s):
    s.replace("{{m}}", "masculin").replace("{{f}}", "feminin").replace("{{n}}", "neutre")
    (s, n) = RGXP_m.subn(r"[\1]", s)
    (s, n) = RGXP_l.subn(r"\2", s)

    (s, n) = RGXP_q.subn(r"\1", s)
    (s, n) = RGXP_r.subn(r"\1", s)

    (s, n) = RGXP_p.subn('', s)
    if s == "": return s

    (s, n) = RGXP_t.subn("\x03\x16" + r"\1" + " :\x03\x16 " + r"\2", s)
    return s.replace("'''", "\x03\x02").replace("''", "\x03\x1f")
