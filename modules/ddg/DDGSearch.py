# coding=utf-8

import http.client
import re
from urllib.parse import quote

import xmlparser

class DDGSearch:
    def __init__(self, terms):
        self.terms = terms
        (res, page) = getPage(terms)
        if res == http.client.OK or res == http.client.SEE_OTHER:
            self.ddgres = xmlparser.parse_string(page)
        else:
            self.ddgres = None

    @property
    def type(self):
        if self.ddgres and self.ddgres.hasNode("Type"):
            return self.ddgres.getFirstNode("Type").getContent()
        else:
            return ""

    @property
    def definition(self):
        if self.ddgres.hasNode("Definition"):
            return self.ddgres.getFirstNode("Definition").getContent()
        else:
            return "Sorry, no definition found for %s" % self.terms

    @property
    def relatedTopics(self):
        try:
            for rt in self.ddgres.getFirstNode("RelatedTopics").getNodes("RelatedTopic"):
                yield rt.getFirstNode("Text").getContent()
        except:
            pass

    @property
    def redirect(self):
        try:
            return self.ddgres.getFirstNode("Redirect").getContent()
        except:
            return None

    @property
    def result(self):
        try:
            node = self.ddgres.getFirstNode("Results").getFirstNode("Result")
            return node.getFirstNode("Text").getContent() + ": " + node.getFirstNode("FirstURL").getContent()
        except:
            return None

    @property
    def answer(self):
        try:
            return striphtml(self.ddgres.getFirstNode("Answer").getContent())
        except:
            return None

    @property
    def abstract(self):
        try:
            return self.ddgres.getNode("Abstract").getContent() + " <" + self.ddgres.getNode("AbstractURL").getContent() + ">"
        except:
            return None


def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data).replace("&#x28;", "/(").replace("&#x29;", ")/").replace("&#x22;", "\"")

def getPage(terms):
    conn = http.client.HTTPConnection("api.duckduckgo.com", timeout=5)
    try:
        conn.request("GET", "/?q=%s&format=xml" % quote(terms))
    except socket.gaierror:
        print ("impossible de récupérer la page %s."%(p))
        return (http.client.INTERNAL_SERVER_ERROR, None)

    res = conn.getresponse()
    data = res.read()

    conn.close()
    return (res.status, data)
