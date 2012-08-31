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
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(define, "d"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(define, "def"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(define, "defini"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(define, "definit"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(define, "define"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(define, "definition"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(search, "search"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(search, "ddg"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(search, "g"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(calculate, "wa"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(calculate, "wfa"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(calculate, "calc"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(wiki, "w"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(wiki, "wf"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(wiki, "wfr"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(wiki, "we"))
    context.hooks.add_hook(context.hooks.cmd_hook, Hook(wiki, "wen"))

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

    s = Wikipedia.Wikipedia(msg.cmd[1], lang)

    res = Response(msg.sender, channel=msg.channel, nomore="No more results")
    for result in s.nextRes:
        res.append_message(result)

    if len(res.messages) > 0:
        return res
    else:
        return Response(msg.sender,
                        "No information about " + msg.cmd[1],
                        msg.channel)
