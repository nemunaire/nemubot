# coding=utf-8

"""Search around various search engine or knowledges database"""

import imp

from nemubot import context
from nemubot.exception import IRCException
from nemubot.hooks import hook

nemubotversion = 3.4

from more import Response

from . import DDGSearch
from . import UrbanDictionnary

@hook("cmd_hook", "define")
def define(msg):
    if not len(msg.args):
        raise IRCException("Indicate a term to define")

    s = DDGSearch.DDGSearch(' '.join(msg.args))

    return Response(s.definition, channel=msg.channel)


@hook("cmd_hook", "search")
def search(msg):
    if not len(msg.args):
        raise IRCException("Indicate a term to search")

    if "!safeoff" in msg.args:
        msg.args.remove("!safeoff")
        safeoff = True
    else:
        safeoff = False

    s = DDGSearch.DDGSearch(' '.join(msg.args), safeoff)

    res = Response(channel=msg.channel, nomore="No more results",
                   count=" (%d more results)")

    res.append_message(s.redirect)
    res.append_message(s.abstract)
    res.append_message(s.result)
    res.append_message(s.answer)

    for rt in s.relatedTopics:
        res.append_message(rt)

    res.append_message(s.definition)

    return res


@hook("cmd_hook", "urbandictionnary")
def udsearch(msg):
    if not len(msg.args):
        raise IRCException("Indicate a term to search")

    s = UrbanDictionnary.UrbanDictionnary(' '.join(msg.args))

    res = Response(channel=msg.channel, nomore="No more results",
                   count=" (%d more definitions)")

    for d in s.definitions:
        res.append_message(d.replace("\n", "  "))

    return res
