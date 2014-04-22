# coding=utf-8

import json
from urllib.parse import quote
from urllib.request import urlopen

class UrbanDictionnary:
    def __init__(self, terms):
        self.terms = terms

        raw = urlopen("http://api.urbandictionary.com/v0/define?term=%s" % quote(terms), timeout=10)
        self.udres = json.loads(raw.read().decode())

    @property
    def result_type(self):
        if self.udres and "result_type" in self.udres:
            return self.udres["result_type"]
        else:
            return ""

    @property
    def definitions(self):
        if self.udres and "list" in self.udres:
            for d in self.udres["list"]:
                yield d["definition"] + "\n" + d["example"]
        else:
            yield "Sorry, no definition found for %s" % self.terms
