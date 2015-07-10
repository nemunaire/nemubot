# coding=utf-8

"""Various network tools (w3m, w3c validator, curl, traceurl, ...)"""

import logging

from nemubot.exception import IRCException
from nemubot.hooks import hook

logger = logging.getLogger("nemubot.module.networking")
nemubotversion = 3.4

from more import Response

from . import isup
from . import page
from . import w3c
from . import watchWebsite
from . import whois

def load(context):
    for mod in [isup, page, w3c, watchWebsite, whois]:
        mod.add_event = context.add_event
        mod.del_event = context.del_event
        mod.save = context.save
        mod.print = print
        mod.send_response = context.send_response
    page.load(context.config, context.add_hook)
    watchWebsite.load(context.data)
    try:
        whois.load(context.config, context.add_hook)
    except ImportError:
        logger.exception("Unable to load netwhois module")


def help_full():
    return "!traceurl /url/: Follow redirections from /url/."


@hook("cmd_hook", "curly")
def cmd_curly(msg):
    if not len(msg.args):
        raise IRCException("Indicate the URL to visit.")

    url = " ".join(msg.args)
    version, status, reason, headers = page.headers(url)

    return Response("Entêtes de la page %s : HTTP/%s, statut : %d %s ; headers : %s" % (url, version, status, reason, ", ".join(["\x03\x02" + h + "\x03\x02: " + v for h, v in headers])), channel=msg.channel)


@hook("cmd_hook", "curl")
def cmd_curl(msg):
    if not len(msg.args):
        raise IRCException("Indicate the URL to visit.")

    res = Response(channel=msg.channel)
    for m in page.fetch(" ".join(msg.args)).split("\n"):
        res.append_message(m)
    return res


@hook("cmd_hook", "w3m")
def cmd_w3m(msg):
    if len(msg.args):
        res = Response(channel=msg.channel)
        for line in page.render(" ".join(msg.args)).split("\n"):
            res.append_message(line)
        return res
    else:
        raise IRCException("Indicate the URL to visit.")


@hook("cmd_hook", "traceurl")
def cmd_traceurl(msg):
    if 1 < len(msg.args) < 5:
        res = list()
        for url in msg.args:
            trace = page.traceURL(url)
            res.append(Response(trace, channel=msg.channel, title="TraceURL"))
        return res
    else:
        raise IRCException("Indicate an URL to trace!")


@hook("cmd_hook", "isup")
def cmd_isup(msg):
    if 1 < len(msg.args) < 5:
        res = list()
        for url in msg.args:
            rep = isup.isup(url)
            if rep:
                res.append(Response("%s is up (response time: %ss)" % (url, rep), channel=msg.channel))
            else:
                res.append(Response("%s is down" % (url), channel=msg.channel))
        return res
    else:
        return Response("Indicate an URL to check!", channel=msg.channel)


@hook("cmd_hook", "w3c")
def cmd_w3c(msg):
    if not len(msg.args):
        raise IRCException("Indicate an URL to validate!")

    headers, validator = w3c.validator(msg.args[0])

    res = Response(channel=msg.channel, nomore="No more error")

    res.append_message("%s: status: %s, %s warning(s), %s error(s)" % (validator["url"], headers["X-W3C-Validator-Status"], headers["X-W3C-Validator-Warnings"], headers["X-W3C-Validator-Errors"]))

    for m in validator["messages"]:
        if "lastLine" not in m:
            res.append_message("%s%s: %s" % (m["type"][0].upper(), m["type"][1:], m["message"]))
        else:
            res.append_message("%s%s on line %s, col %s: %s" % (m["type"][0].upper(), m["type"][1:], m["lastLine"], m["lastColumn"], m["message"]))

    return res



@hook("cmd_hook", "watch", data="diff")
@hook("cmd_hook", "updown", data="updown")
def cmd_watch(msg, diffType="diff"):
    if not len(msg.args):
        raise IRCException("indicate an URL to watch!")

    return watchWebsite.add_site(msg.args[0], msg.frm, msg.channel, msg.server, diffType)


@hook("cmd_hook", "unwatch")
def cmd_unwatch(msg):
    if not len(msg.args):
        raise IRCException("which URL should I stop watching?")

    return watchWebsite.del_site(msg.args[0], msg.frm, msg.channel, msg.frm_owner)
