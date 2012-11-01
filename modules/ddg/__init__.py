# coding=utf-8

import imp

nemubotversion = 3.2

from . import DDGSearch
from . import WFASearch
from . import Wikipedia

def load(context):
    global CONF
    WFASearch.CONF = CONF

    from hooks import Hook
    add_hook("cmd_hook", Hook(define, "d"))
    add_hook("cmd_hook", Hook(define, "def"))
    add_hook("cmd_hook", Hook(define, "defini"))
    add_hook("cmd_hook", Hook(define, "definit"))
    add_hook("cmd_hook", Hook(define, "define"))
    add_hook("cmd_hook", Hook(define, "definition"))
    add_hook("cmd_hook", Hook(search, "search"))
    add_hook("cmd_hook", Hook(search, "ddg"))
    add_hook("cmd_hook", Hook(search, "g"))
    add_hook("cmd_hook", Hook(calculate, "wa"))
    add_hook("cmd_hook", Hook(calculate, "wfa"))
    add_hook("cmd_hook", Hook(calculate, "calc"))
    add_hook("cmd_hook", Hook(wiki, "w"))
    add_hook("cmd_hook", Hook(wiki, "wf"))
    add_hook("cmd_hook", Hook(wiki, "wfr"))
    add_hook("cmd_hook", Hook(wiki, "we"))
    add_hook("cmd_hook", Hook(wiki, "wen"))

def reload():
    imp.reload(DDGSearch)
    imp.reload(WFASearch)
    imp.reload(Wikipedia)


def define(msg):
    if len(msg.cmd) <= 1:
        return Response(msg.sender,
                        "Indicate a term to define",
                        msg.channel, nick=msg.nick)

    s = DDGSearch.DDGSearch(' '.join(msg.cmd[1:]))

    res = Response(msg.sender, channel=msg.channel)

    res.append_message(s.definition)

    return res


def search(msg):
    if len(msg.cmd) <= 1:
        return Response(msg.sender,
                        "Indicate a term to search",
                        msg.channel, nick=msg.nick)

    s = DDGSearch.DDGSearch(' '.join(msg.cmd[1:]))

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
    if len(msg.cmd) <= 1:
        return Response(msg.sender,
                        "Indicate a calcul to compute",
                        msg.channel, nick=msg.nick)

    s = WFASearch.WFASearch(' '.join(msg.cmd[1:]))

    if s.success:
        res = Response(msg.sender, channel=msg.channel, nomore="No more results")
        for result in s.nextRes:
            res.append_message(result)
        res.messages.pop(0)
        return res
    else:
        return Response(msg.sender, s.error, msg.channel)


def wiki(msg):
    if len(msg.cmd) <= 1:
        return Response(msg.sender,
                        "Indicate a term to search",
                        msg.channel, nick=msg.nick)
    if msg.cmd[0] == "w" or msg.cmd[0] == "wf" or msg.cmd[0] == "wfr":
        lang = "fr"
    else:
        lang = "en"

    s = Wikipedia.Wikipedia(' '.join(msg.cmd[1:]), lang)

    res = Response(msg.sender, channel=msg.channel, nomore="No more results")
    for result in s.nextRes:
        res.append_message(result)

    if len(res.messages) > 0:
        return res
    else:
        return Response(msg.sender,
                        "No information about " + msg.cmd[1],
                        msg.channel)
