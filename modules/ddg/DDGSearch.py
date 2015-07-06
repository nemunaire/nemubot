# coding=utf-8

from urllib.parse import quote

from nemubot.tools import web
from nemubot.tools.xmlparser import parse_string


class DDGSearch:

    def __init__(self, terms, safeoff=False):
        self.terms = terms

        self.ddgres = web.getXML(
            "https://api.duckduckgo.com/?q=%s&format=xml&no_redirect=1%s" %
            (quote(terms), "&kp=-1" if safeoff else ""),
            timeout=10)

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
            return web.striphtml(self.ddgres.getFirstNode("Answer").getContent())
        except:
            return None

    @property
    def abstract(self):
        try:
            if self.ddgres.getNode("Abstract").getContent() != "":
                return self.ddgres.getNode("Abstract").getContent() + " <" + self.ddgres.getNode("AbstractURL").getContent() + ">"
            else:
                return None
        except:
            return None
