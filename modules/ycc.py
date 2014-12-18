# coding=utf-8

"""URL reducer module"""

import re
from urllib.parse import urlparse
from urllib.parse import quote

from hooks import hook
from message import TextMessage
from tools import web

nemubotversion = 3.4


def help_full():
    return ("!ycc [<url>]: with an argument, reduce the given <url> thanks to "
            "ycc.fr; without argument, reduce the last URL said on the current"
            " channel.")

LAST_URLS = dict()


def reduce(url):
    """Ask YCC website to reduce given URL

    Argument:
    url -- the URL to reduce
    """

    snd_url = "http://ycc.fr/redirection/create/" + quote(url, "/:%@&=?")
    print_debug(snd_url)
    return web.getURLContent(snd_url)


def gen_response(res, msg, srv):
    if res is None:
        raise IRCException("mauvaise URL : %s" % srv)
    else:
        return TextMessage("URL pour %s : %s" % (srv, res), server=None,
                           to=msg.to_response)


@hook("cmd_hook", "ycc")
def cmd_ycc(msg):
    minify = list()

    if len(msg.cmds) == 1:
        global LAST_URLS
        if msg.channel in LAST_URLS and len(LAST_URLS[msg.channel]) > 0:
            minify.append(LAST_URLS[msg.channel].pop())
        else:
            raise IRCException("je n'ai pas d'autre URL à réduire.")

    if len(msg.cmds) > 5:
        raise IRCException("je ne peux pas réduire autant d'URL d'un seul coup.")
    else:
        minify += msg.cmds[1:]

    res = list()
    for url in minify:
        o = urlparse(url, "http")
        if o.scheme != "":
            minief_url = reduce(url)
            if o.netloc == "":
                res.append(gen_response(minief_url, msg, o.scheme))
            else:
                res.append(gen_response(minief_url, msg, o.netloc))
        else:
            res.append(gen_response(None, msg, url))
    return res


@hook("msg_default")
def parselisten(msg):
    parseresponse(msg)
    return None


@hook("all_post")
def parseresponse(msg):
    global LAST_URLS
    try:
        urls = re.findall("([a-zA-Z0-9+.-]+:(?://)?[^ ]+)", msg.text)
        for url in urls:
            o = urlparse(url)
            if o.scheme != "":
                if o.netloc == "ycc.fr" or (o.netloc == "" and
                                            len(o.path) < 10):
                    continue
                if msg.channel not in LAST_URLS:
                    LAST_URLS[msg.channel] = list()
                LAST_URLS[msg.channel].append(url)
    except:
        pass
    return msg
