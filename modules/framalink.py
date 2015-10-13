"""URL reducer module"""

# PYTHON STUFFS #######################################################

import re
import json
from urllib.parse import urlparse
from urllib.parse import quote

from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.message import Text
from nemubot.tools import web


# MODULE FUCNTIONS ####################################################

def default_reducer(url, data):
    snd_url = url + quote(data, "/:%@&=?")
    return web.getURLContent(snd_url)

def framalink_reducer(url, data):
    json_data =  json.loads(web.getURLContent(url, "lsturl="
        + quote(data, "/:%@&=?"),
        header={"Content-Type": "application/x-www-form-urlencoded"}))
    return json_data['short']

# MODULE VARIABLES ####################################################

PROVIDERS = {
    "tinyurl": (default_reducer, "http://tinyurl.com/api-create.php?url="),
    "ycc": (default_reducer, "http://ycc.fr/redirection/create/"),
    "framalink": (framalink_reducer, "https://frama.link/a?format=json")
}
DEFAULT_PROVIDER = "framalink"

PROVIDERS_NETLOC = [urlparse(web.getNormalizedURL(url), "http").netloc for f, url in PROVIDERS.values()]

# LOADING #############################################################

def load(context):
    global DEFAULT_PROVIDER

    if "provider" in context.config:
        if context.config["provider"] == "custom":
            PROVIDERS["custom"] = context.config["provider_url"]
        DEFAULT_PROVIDER = context.config["provider"]


# MODULE CORE #########################################################

def reduce(url):
    """Ask the url shortner website to reduce given URL

    Argument:
    url -- the URL to reduce
    """
    return PROVIDERS[DEFAULT_PROVIDER][0](PROVIDERS[DEFAULT_PROVIDER][1], url)

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
    if hasattr(msg, "text") and msg.text:
        urls = re.findall("([a-zA-Z0-9+.-]+:(?://)?[^ :]+)", msg.text)
        for url in urls:
            o = urlparse(web._getNormalizedURL(url), "http")

            # Skip short URLs
            if o.netloc == "" or o.netloc in PROVIDERS or len(o.netloc) + len(o.path) < 17:
                continue

            for recv in msg.receivers:
                if recv not in LAST_URLS:
                    LAST_URLS[recv] = list()
                LAST_URLS[recv].append(url)
    return msg


# MODULE INTERFACE ####################################################

@hook("cmd_hook", "framalink",
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
        o = urlparse(web.getNormalizedURL(url), "http")
        minief_url = reduce(url)
        if o.netloc == "":
            res.append(gen_response(minief_url, msg, o.scheme))
        else:
            res.append(gen_response(minief_url, msg, o.netloc))
    return res
