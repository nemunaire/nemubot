# coding=utf-8

"""Search around various search engine or knowledges database"""

import imp

from nemubot import context
from nemubot.hooks import hook

nemubotversion = 3.4

from more import Response

from . import DDGSearch
from . import UrbanDictionnary

@hook("cmd_hook", "define")
def define(msg):
    if len(msg.cmds) <= 1:
        return Response("Indicate a term to define",
                        msg.channel, nick=msg.nick)

    s = DDGSearch.DDGSearch(' '.join(msg.cmds[1:]))

    res = Response(channel=msg.channel)

    res.append_message(s.definition)

    return res

@hook("cmd_hook", "search")
def search(msg):
    if len(msg.cmds) <= 1:
        return Response("Indicate a term to search",
                        msg.channel, nick=msg.nick)

    s = DDGSearch.DDGSearch(' '.join(msg.cmds[1:]))

    res = Response(channel=msg.channel, nomore="No more results",
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
        return Response("Indicate a term to search",
                        msg.channel, nick=msg.nick)

    s = UrbanDictionnary.UrbanDictionnary(' '.join(msg.cmds[1:]))

    res = Response(channel=msg.channel, nomore="No more results",
                   count=" (%d more definitions)")

    for d in s.definitions:
        res.append_message(d)

    return res
