# coding=utf-8

from urllib.parse import quote

from tools import web


class WFASearch:
    def __init__(self, terms):
        self.terms = terms
        try:
            url = ("http://api.wolframalpha.com/v2/query?input=%s&appid=%s" %
                   (quote(terms), CONF.getNode("wfaapi")["key"]))
            self.wfares = web.getXML(url)
        except (TypeError, KeyError):
            print ("You need a Wolfram|Alpha API key in order to use this "
                   "module. Add it to the module configuration file:\n<wfaapi"
                   " key=\"XXXXXX-XXXXXXXXXX\" />\nRegister at "
                   "http://products.wolframalpha.com/api/")
            self.wfares = None

    @property
    def success(self):
        try:
            return self.wfares["success"] == "true"
        except:
            return False

    @property
    def error(self):
        if self.wfares is None:
            return "An error occurs during computation."
        elif self.wfares["error"] == "true":
            return ("An error occurs during computation: " +
                    self.wfares.getNode("error").getNode("msg").getContent())
        elif self.wfares.hasNode("didyoumeans"):
            start = "Did you mean: "
            tag = "didyoumean"
            end = "?"
        elif self.wfares.hasNode("tips"):
            start = "Tips: "
            tag = "tip"
            end = ""
        elif self.wfares.hasNode("relatedexamples"):
            start = "Related examples: "
            tag = "relatedexample"
            end = ""
        elif self.wfares.hasNode("futuretopic"):
            return self.wfares.getNode("futuretopic")["msg"]
        else:
            return "An error occurs during computation"
        proposal = list()
        for dym in self.wfares.getNode(tag + "s").getNodes(tag):
            if tag == "tip":
                proposal.append(dym["text"])
            elif tag == "relatedexample":
                proposal.append(dym["desc"])
            else:
                proposal.append(dym.getContent())
        return start + ', '.join(proposal) + end

    @property
    def nextRes(self):
        try:
            for node in self.wfares.getNodes("pod"):
                for subnode in node.getNodes("subpod"):
                    if subnode.getFirstNode("plaintext").getContent() != "":
                        yield (node["title"] + " " + subnode["title"] + ": " +
                               subnode.getFirstNode("plaintext").getContent())
        except IndexError:
            pass
