"""URL reducer module"""

# PYTHON STUFFS #######################################################

import re
from urllib.parse import urlparse
from urllib.parse import quote

from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.message import Text
from nemubot.tools import web


# MODULE VARIABLES ####################################################

PROVIDERS = {
    "tinyurl": "http://tinyurl.com/api-create.php?url=",
    "ycc": "http://ycc.fr/redirection/create/",
}
DEFAULT_PROVIDER = "ycc"


# LOADING #############################################################

def load(context):
    global DEFAULT_PROVIDER

    if "provider" in context.config:
        if context.config["provider"] == "custom":
            PROVIDERS["custom"] = context.config["provider_url"]
        DEFAULT_PROVIDER = context.config["provider"]


# MODULE CORE #########################################################

def reduce(url):
    """Ask YCC website to reduce given URL

    Argument:
    url -- the URL to reduce
    """

    snd_url = PROVIDERS[DEFAULT_PROVIDER] + quote(url, "/:%@&=?")
    return web.getURLContent(snd_url)


def gen_response(res, msg, srv):
    if res is None:
        raise IRCException("bad URL : %s" % srv)
    else:
        return Text("URL for %s: %s" % (srv, res), server=None,
                    to=msg.to_response)


## URL stack

LAST_URLS = dict()


@hook("msg_default")
def parselisten(msg):
    parseresponse(msg)
    return None


@hook("all_post")
def parseresponse(msg):
    global LAST_URLS
    try:
        urls = re.findall("([a-zA-Z0-9+.-]+:(?://)?[^ :]+)", msg.text)
        for url in urls:
            o = urlparse(url)
            if o.scheme != "":
                if o.netloc == "ycc.fr" or o.netloc == "tinyurl.com" or (
                        o.netloc == "" and len(o.path) < 10):
                    continue
                for recv in msg.receivers:
                    if recv not in LAST_URLS:
                        LAST_URLS[recv] = list()
                    LAST_URLS[recv].append(url)
    except:
        pass
    return msg


# MODULE INTERFACE ####################################################

@hook("cmd_hook", "tinyurl",
      help="Reduce any given URL",
      help_usage={None: "Reduce the last URL said on the channel",
                  "URL [URL ...]": "Reduce the given URL(s)"})
def cmd_reduceurl(msg):
    minify = list()

    if not len(msg.args):
        global LAST_URLS
        if msg.channel in LAST_URLS and len(LAST_URLS[msg.channel]) > 0:
            minify.append(LAST_URLS[msg.channel].pop())
        else:
            raise IRCException("I have no more URL to reduce.")

    if len(msg.args) > 4:
        raise IRCException("I cannot reduce as much URL at once.")
    else:
        minify += msg.args

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
