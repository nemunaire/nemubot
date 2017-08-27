"""Performing search and calculation"""

# PYTHON STUFFS #######################################################

from urllib.parse import quote
import re

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from nemubot.module.more import Response


# LOADING #############################################################

URL_API = "http://api.wolframalpha.com/v2/query?input=%%s&format=plaintext&appid=%s"

def load(context):
    global URL_API
    if not context.config or "apikey" not in context.config:
        raise ImportError ("You need a Wolfram|Alpha API key in order to use "
                           "this module. Add it to the module configuration: "
                           "\n<module name=\"wolframalpha\" "
                           "apikey=\"XXXXXX-XXXXXXXXXX\" />\n"
                           "Register at http://products.wolframalpha.com/api/")
    URL_API = URL_API % quote(context.config["apikey"]).replace("%", "%%")


# MODULE CORE #########################################################

class WFAResults:

    def __init__(self, terms):
        self.wfares = web.getXML(URL_API % quote(terms),
                                 timeout=12)


    @property
    def success(self):
        try:
            return self.wfares.documentElement.hasAttribute("success") and self.wfares.documentElement.getAttribute("success") == "true"
        except:
            return False


    @property
    def error(self):
        if self.wfares is None:
            return "An error occurs during computation."
        elif self.wfares.documentElement.hasAttribute("error") and self.wfares.documentElement.getAttribute("error") == "true":
            return ("An error occurs during computation: " +
                    self.wfares.getElementsByTagName("error")[0].getElementsByTagName("msg")[0].firstChild.nodeValue)
        elif len(self.wfares.getElementsByTagName("didyoumeans")):
            start = "Did you mean: "
            tag = "didyoumean"
            end = "?"
        elif len(self.wfares.getElementsByTagName("tips")):
            start = "Tips: "
            tag = "tip"
            end = ""
        elif len(self.wfares.getElementsByTagName("relatedexamples")):
            start = "Related examples: "
            tag = "relatedexample"
            end = ""
        elif len(self.wfares.getElementsByTagName("futuretopic")):
            return self.wfares.getElementsByTagName("futuretopic")[0].getAttribute("msg")
        else:
            return "An error occurs during computation"

        proposal = list()
        for dym in self.wfares.getElementsByTagName(tag):
            if tag == "tip":
                proposal.append(dym.getAttribute("text"))
            elif tag == "relatedexample":
                proposal.append(dym.getAttribute("desc"))
            else:
                proposal.append(dym.firstChild.nodeValue)

        return start + ', '.join(proposal) + end


    @property
    def results(self):
        for node in self.wfares.getElementsByTagName("pod"):
            for subnode in node.getElementsByTagName("subpod"):
                if subnode.getElementsByTagName("plaintext")[0].firstChild:
                    yield (node.getAttribute("title") +
                           ((" / " + subnode.getAttribute("title")) if subnode.getAttribute("title") else "") + ": " +
                           "; ".join(subnode.getElementsByTagName("plaintext")[0].firstChild.nodeValue.split("\n")))


# MODULE INTERFACE ####################################################

@hook.command("calculate",
      help="Perform search and calculation using WolframAlpha",
      help_usage={
          "TERM": "Look at the given term on WolframAlpha",
          "CALCUL": "Perform the computation over WolframAlpha service",
      })
def calculate(msg):
    if not len(msg.args):
        raise IMException("Indicate a calcul to compute")

    s = WFAResults(' '.join(msg.args))

    if not s.success:
        raise IMException(s.error)

    res = Response(channel=msg.channel, nomore="No more results")

    for result in s.results:
        res.append_message(re.sub(r' +', ' ', result))
    if len(res.messages):
        res.messages.pop(0)

    return res
