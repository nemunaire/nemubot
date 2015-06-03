# coding=utf-8

from urllib.parse import quote

from nemubot import context
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools import web

nemubotversion = 4.0

from more import Response

URL_API = "http://api.wolframalpha.com/v2/query?input=%%s&appid=%s"

def load(context):
    global URL_API
    if not context.config or not context.config.hasAttribute("apikey"):
        raise ImportError ("You need a Wolfram|Alpha API key in order to use "
                           "this module. Add it to the module configuration: "
                           "\n<module name=\"wolframalpha\" "
                           "apikey=\"XXXXXX-XXXXXXXXXX\" />\n"
                           "Register at http://products.wolframalpha.com/api/")
    URL_API = URL_API % quote(context.config["apikey"]).replace("%", "%%")


class WFASearch:
    def __init__(self, terms):
        self.terms = terms
        self.wfares = web.getXML(URL_API % quote(terms))

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


@hook("cmd_hook", "calculate")
def calculate(msg):
    if not len(msg.args):
        raise IRCException("Indicate a calcul to compute")

    s = WFASearch(' '.join(msg.args))

    if s.success:
        res = Response(channel=msg.channel, nomore="No more results")
        for result in s.nextRes:
            res.append_message(result)
        if (len(res.messages) > 0):
            res.messages.pop(0)
        return res
    else:
        return Response(s.error, msg.channel)
