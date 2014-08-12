# coding=utf-8

import imp

from hooks import hook

nemubotversion = 3.3

from . import DDGSearch
from . import UrbanDictionnary
from . import WFASearch
from . import Wikipedia

def load(context):
    global CONF
    WFASearch.CONF = CONF

def reload():
    imp.reload(DDGSearch)
    imp.reload(UrbanDictionnary)
    imp.reload(WFASearch)
    imp.reload(Wikipedia)


@hook("cmd_hook", "define")
def define(msg):
    if len(msg.cmds) <= 1:
        return Response(msg.sender,
                        "Indicate a term to define",
                        msg.channel, nick=msg.nick)

    s = DDGSearch.DDGSearch(' '.join(msg.cmds[1:]))

    res = Response(msg.sender, channel=msg.channel)

    res.append_message(s.definition)

    return res

@hook("cmd_hook", "search")
def search(msg):
    if len(msg.cmds) <= 1:
        return Response(msg.sender,
                        "Indicate a term to search",
                        msg.channel, nick=msg.nick)

    s = DDGSearch.DDGSearch(' '.join(msg.cmds[1:]))

    res = Response(msg.sender, channel=msg.channel, nomore="No more results",
                   count=" (%d more results)")

    res.append_message(s.redirect)
    res.append_message(s.abstract)
    res.append_message(s.result)
    res.append_message(s.answer)

    for rt in s.relatedTopics:
        res.append_message(rt)

    return res


@hook("cmd_hook", "urbandictionnary")
def udsearch(msg):
    if len(msg.cmds) <= 1:
        return Response(msg.sender,
                        "Indicate a term to search",
                        msg.channel, nick=msg.nick)

    s = UrbanDictionnary.UrbanDictionnary(' '.join(msg.cmds[1:]))

    res = Response(msg.sender, channel=msg.channel, nomore="No more results",
                   count=" (%d more definitions)")

    for d in s.definitions:
        res.append_message(d)

    return res


@hook("cmd_hook", "calculate")
def calculate(msg):
    if len(msg.cmds) <= 1:
        return Response(msg.sender,
                        "Indicate a calcul to compute",
                        msg.channel, nick=msg.nick)

    s = WFASearch.WFASearch(' '.join(msg.cmds[1:]))

    if s.success:
        res = Response(msg.sender, channel=msg.channel, nomore="No more results")
        for result in s.nextRes:
            res.append_message(result)
        if (len(res.messages) > 0):
            res.messages.pop(0)
        return res
    else:
        return Response(msg.sender, s.error, msg.channel)


@hook("cmd_hook", "wikipedia")
def wikipedia(msg):
    return wiki("wikipedia.org", 0, msg)

@hook("cmd_hook", "wiktionary")
def wiktionary(msg):
    return wiki("wiktionary.org", 1, msg)

@hook("cmd_hook", "etymology")
def wiktionary(msg):
    return wiki("wiktionary.org", 0, msg)

def wiki(site, section, msg):
    if len(msg.cmds) <= 1:
        return Response(msg.sender,
                        "Indicate a term to search",
                        msg.channel, nick=msg.nick)
    if len(msg.cmds) > 2 and len(msg.cmds[1]) < 4:
        lang = msg.cmds[1]
        extract = 2
    else:
        lang = "fr"
        extract = 1

    s = Wikipedia.Wikipedia(' '.join(msg.cmds[extract:]), lang, site, section)

    res = Response(msg.sender, channel=msg.channel, nomore="No more results")
    if site == "wiktionary.org":
        tout = [result for result in s.nextRes if result.find("\x03\x16 :\x03\x16 ") != 0]
        if len(tout) > 0:
            defI=1
            for t in tout:
                if t.find("# ") == 0:
                    t = t.replace("# ", "%d. " % defI)
                    defI += 1
                elif t.find("#* ") == 0:
                    t = t.replace("#* ", "  * ")
                res.append_message(t)
    else:
        for result in s.nextRes:
            res.append_message(result)

    if len(res.messages) > 0:
        return res
    else:
        return Response(msg.sender,
                        "No information about " + " ".join(msg.cmds[extract:]),
                        msg.channel)
