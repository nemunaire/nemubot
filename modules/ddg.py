"""Search around DuckDuckGo search engine"""

# PYTHON STUFFS #######################################################

from urllib.parse import quote

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response

# MODULE CORE #########################################################

def do_search(terms):
    if "!safeoff" in terms:
        terms.remove("!safeoff")
        safeoff = True
    else:
        safeoff = False

    sterm = " ".join(terms)
    return DDGResult(sterm, web.getJSON(
        "https://api.duckduckgo.com/?q=%s&format=json&no_redirect=1%s" %
        (quote(sterm), "&kp=-1" if safeoff else "")))


class DDGResult:

    def __init__(self, terms, res):
        if res is None:
            raise IMException("An error occurs during search")

        self.terms = terms
        self.ddgres = res


    @property
    def type(self):
        if not self.ddgres or "Type" not in self.ddgres:
            return ""
        return self.ddgres["Type"]


    @property
    def definition(self):
        if "Definition" not in self.ddgres or not self.ddgres["Definition"]:
            return "Sorry, no definition found for %s." % self.terms
        return self.ddgres["Definition"] + " <" + self.ddgres["DefinitionURL"] + "> from " + self.ddgres["DefinitionSource"]


    @property
    def relatedTopics(self):
        if "RelatedTopics" in self.ddgres:
            for rt in self.ddgres["RelatedTopics"]:
                if "Text" in rt:
                    yield rt["Text"] + " <" + rt["FirstURL"] + ">"
                elif "Topics" in rt:
                    yield rt["Name"] + ": " + "; ".join([srt["Text"] + " <" + srt["FirstURL"] + ">" for srt in rt["Topics"]])


    @property
    def redirect(self):
        if "Redirect" not in self.ddgres or not self.ddgres["Redirect"]:
            return None
        return self.ddgres["Redirect"]


    @property
    def entity(self):
        if "Entity" not in self.ddgres or not self.ddgres["Entity"]:
            return None
        return self.ddgres["Entity"]


    @property
    def heading(self):
        if "Heading" not in self.ddgres or not self.ddgres["Heading"]:
            return " ".join(self.terms)
        return self.ddgres["Heading"]


    @property
    def result(self):
        if "Results" in self.ddgres:
            for res in self.ddgres["Results"]:
                yield res["Text"] + " <" + res["FirstURL"] + ">"


    @property
    def answer(self):
        if "Answer" not in self.ddgres or not self.ddgres["Answer"]:
            return None
        return web.striphtml(self.ddgres["Answer"])


    @property
    def abstract(self):
        if "Abstract" not in self.ddgres or not self.ddgres["Abstract"]:
            return None
        return self.ddgres["AbstractText"] + " <" + self.ddgres["AbstractURL"] + "> from " + self.ddgres["AbstractSource"]


# MODULE INTERFACE ####################################################

@hook("cmd_hook", "define")
def define(msg):
    if not len(msg.args):
        raise IMException("Indicate a term to define")

    s = do_search(msg.args)

    if not s.definition:
        raise IMException("no definition found for '%s'." % " ".join(msg.args))

    return Response(s.definition, channel=msg.channel)

@hook("cmd_hook", "search")
def search(msg):
    if not len(msg.args):
        raise IMException("Indicate a term to search")

    s = do_search(msg.args)

    res = Response(channel=msg.channel, nomore="No more results",
                   count=" (%d more results)")

    res.append_message(s.redirect)
    res.append_message(s.answer)
    res.append_message(s.abstract)
    res.append_message([r for r in s.result])

    for rt in s.relatedTopics:
        res.append_message(rt)

    res.append_message(s.definition)

    return res
