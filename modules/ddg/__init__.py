# coding=utf-8

import imp

nemubotversion = 3.3

from . import DDGSearch
from . import WFASearch
from . import Wikipedia

def load(context):
    global CONF
    WFASearch.CONF = CONF

    from hooks import Hook
    add_hook("cmd_hook", Hook(define, "define"))
    add_hook("cmd_hook", Hook(search, "search"))
    add_hook("cmd_hook", Hook(search, "ddg"))
    add_hook("cmd_hook", Hook(search, "g"))
    add_hook("cmd_hook", Hook(calculate, "wa"))
    add_hook("cmd_hook", Hook(calculate, "calc"))
    add_hook("cmd_hook", Hook(wiki, "dico"))
    add_hook("cmd_hook", Hook(wiki, "wiki"))

def reload():
    imp.reload(DDGSearch)
    imp.reload(WFASearch)
    imp.reload(Wikipedia)


def define(msg):
    if len(msg.cmds) <= 1:
        return Response(msg.sender,
                        "Indicate a term to define",
                        msg.channel, nick=msg.nick)

    s = DDGSearch.DDGSearch(' '.join(msg.cmds[1:]))

    res = Response(msg.sender, channel=msg.channel)

    res.append_message(s.definition)

    return res


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


def wiki(msg):
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
    if msg.cmds[0] == "dico":
        site = "wiktionary.org"
        section = 1
    else:
        site = "wikipedia.org"
        section = 0

    s = Wikipedia.Wikipedia(' '.join(msg.cmds[extract:]), lang, site, section)

    res = Response(msg.sender, channel=msg.channel, nomore="No more results")
    if site == "wiktionary.org":
        tout = [result for result in s.nextRes if result.find("\x03\x16 :\x03\x16 ") != 0]
        if len(tout) > 0:
            tout.remove(tout[0])
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
                        "No information about " + " ".join(msg.cmds[1:]),
                        msg.channel)
