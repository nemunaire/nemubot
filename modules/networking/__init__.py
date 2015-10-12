"""Various network tools (w3m, w3c validator, curl, traceurl, ...)"""

# PYTHON STUFFS #######################################################

import logging
import re

from nemubot.exception import IRCException
from nemubot.hooks import hook

from more import Response

from . import isup
from . import page
from . import w3c
from . import watchWebsite
from . import whois

logger = logging.getLogger("nemubot.module.networking")


# LOADING #############################################################

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


# MODULE INTERFACE ####################################################

@hook("cmd_hook", "title",
      help="Retrieve webpage's title",
      help_usage={"URL": "Display the title of the given URL"})
def cmd_title(msg):
    if not len(msg.args):
        raise IRCException("Indicate the URL to visit.")

    url = " ".join(msg.args)
    res = re.search("<title>(.*?)</title>", page.fetch(" ".join(msg.args)), re.DOTALL)

    if res is None:
        raise IRCException("The page %s has no title" % url)
    else:
        return Response("%s: %s" % (url, res.group(1).replace("\n", " ")), channel=msg.channel)


@hook("cmd_hook", "curly",
      help="Retrieve webpage's headers",
      help_usage={"URL": "Display HTTP headers of the given URL"})
def cmd_curly(msg):
    if not len(msg.args):
        raise IRCException("Indicate the URL to visit.")

    url = " ".join(msg.args)
    version, status, reason, headers = page.headers(url)

    return Response("Entêtes de la page %s : HTTP/%s, statut : %d %s ; headers : %s" % (url, version, status, reason, ", ".join(["\x03\x02" + h + "\x03\x02: " + v for h, v in headers])), channel=msg.channel)


@hook("cmd_hook", "curl",
      help="Retrieve webpage's body",
      help_usage={"URL": "Display raw HTTP body of the given URL"})
def cmd_curl(msg):
    if not len(msg.args):
        raise IRCException("Indicate the URL to visit.")

    res = Response(channel=msg.channel)
    for m in page.fetch(" ".join(msg.args)).split("\n"):
        res.append_message(m)
    return res


@hook("cmd_hook", "w3m",
      help="Retrieve and format webpage's content",
      help_usage={"URL": "Display and format HTTP content of the given URL"})
def cmd_w3m(msg):
    if not len(msg.args):
        raise IRCException("Indicate the URL to visit.")
    res = Response(channel=msg.channel)
    for line in page.render(" ".join(msg.args)).split("\n"):
        res.append_message(line)
    return res


@hook("cmd_hook", "traceurl",
      help="Follow redirections of a given URL and display each step",
      help_usage={"URL": "Display redirections steps for the given URL"})
def cmd_traceurl(msg):
    if not len(msg.args):
        raise IRCException("Indicate an URL to trace!")

    res = list()
    for url in msg.args[:4]:
        try:
            trace = page.traceURL(url)
            res.append(Response(trace, channel=msg.channel, title="TraceURL"))
        except:
            pass
    return res


@hook("cmd_hook", "isup",
      help="Check if a website is up",
      help_usage={"DOMAIN": "Check if a DOMAIN is up"})
def cmd_isup(msg):
    if not len(msg.args):
        raise IRCException("Indicate an domain name to check!")

    res = list()
    for url in msg.args[:4]:
        rep = isup.isup(url)
        if rep:
            res.append(Response("%s is up (response time: %ss)" % (url, rep), channel=msg.channel))
        else:
            res.append(Response("%s is down" % (url), channel=msg.channel))
    return res


@hook("cmd_hook", "w3c",
      help="Perform a w3c HTML validator check",
      help_usage={"URL": "Do W3C HTML validation on the given URL"})
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



@hook("cmd_hook", "watch", data="diff",
      help="Alert on webpage change",
      help_usage={"URL": "Watch the given URL and alert when it changes"})
@hook("cmd_hook", "updown", data="updown",
      help="Alert on server availability change",
      help_usage={"URL": "Watch the given domain and alert when it availability status changes"})
def cmd_watch(msg, diffType="diff"):
    if not len(msg.args):
        raise IRCException("indicate an URL to watch!")

    return watchWebsite.add_site(msg.args[0], msg.frm, msg.channel, msg.server, diffType)


@hook("cmd_hook", "listwatch",
      help="List URL watched for the channel",
      help_usage={None: "List URL watched for the channel"})
def cmd_listwatch(msg):
    wl = watchWebsite.watchedon(msg.channel)
    if len(wl):
        return Response(wl, channel=msg.channel, title="URL watched on this channel")
    else:
        return Response("No URL are currently watched. Use !watch URL to watch one.", channel=msg.channel)


@hook("cmd_hook", "unwatch",
      help="Unwatch a previously watched URL",
      help_usage={"URL": "Unwatch the given URL"})
def cmd_unwatch(msg):
    if not len(msg.args):
        raise IRCException("which URL should I stop watching?")

    for arg in msg.args:
        return watchWebsite.del_site(arg, msg.frm, msg.channel, msg.frm_owner)
