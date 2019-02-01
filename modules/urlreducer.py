"""URL reducer module"""

# PYTHON STUFFS #######################################################

import re
import json
from urllib.parse import urlparse
from urllib.parse import quote

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.message import Text
from nemubot.tools import web


# MODULE FUNCTIONS ####################################################

def default_reducer(url, data):
    snd_url = url + quote(data, "/:%@&=?")
    return web.getURLContent(snd_url)


def ycc_reducer(url, data):
    return "https://ycc.fr/%s" % default_reducer(url, data)

def lstu_reducer(url, data):
    json_data = json.loads(web.getURLContent(url, "lsturl=" + quote(data),
        header={"Content-Type": "application/x-www-form-urlencoded"}))
    if 'short' in json_data:
        return json_data['short']
    elif 'msg' in json_data:
        raise IMException("Error: %s" % json_data['msg'])
    else:
        IMException("An error occured while shortening %s." % data)

# MODULE VARIABLES ####################################################

PROVIDERS = {
    "tinyurl": (default_reducer, "https://tinyurl.com/api-create.php?url="),
    "ycc": (ycc_reducer, "https://ycc.fr/redirection/create/"),
    "framalink": (lstu_reducer, "https://frama.link/a?format=json"),
    "huitre": (lstu_reducer, "https://huit.re/a?format=json"),
    "lstu": (lstu_reducer, "https://lstu.fr/a?format=json"),
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

def reduce_inline(txt, provider=None):
    for url in re.findall("([a-zA-Z0-9+.-]+:(?://)?(?:[^ :/]+:[0-9]+)?[^ :]+)", txt):
        txt = txt.replace(url, reduce(url, provider))
    return txt


def reduce(url, provider=None):
    """Ask the url shortner website to reduce given URL

    Argument:
    url -- the URL to reduce
    """
    if provider is None:
        provider = DEFAULT_PROVIDER
    return PROVIDERS[provider][0](PROVIDERS[provider][1], url)


def gen_response(res, msg, srv):
    if res is None:
        raise IMException("bad URL : %s" % srv)
    else:
        return Text("URL for %s: %s" % (srv, res), server=None,
                    to=msg.to_response)


## URL stack

LAST_URLS = dict()


@hook.message()
def parselisten(msg):
    global LAST_URLS
    if hasattr(msg, "message") and isinstance(msg.message, str):
        urls = re.findall("([a-zA-Z0-9+.-]+:(?://)?(?:[^ :/]+:[0-9]+)?[^ :]+)",
                          msg.message)
        for url in urls:
            o = urlparse(web._getNormalizedURL(url), "http")

            # Skip short URLs
            if (o.netloc == "" or o.netloc in PROVIDERS or
                    len(o.netloc) + len(o.path) < 17):
                continue

            for recv in msg.to:
                if recv not in LAST_URLS:
                    LAST_URLS[recv] = list()
                LAST_URLS[recv].append(url)


@hook.post()
def parseresponse(msg):
    global LAST_URLS
    if hasattr(msg, "text") and isinstance(msg.text, str):
        urls = re.findall("([a-zA-Z0-9+.-]+:(?://)?(?:[^ :/]+:[0-9]+)?[^ :]+)",
                          msg.text)
        for url in urls:
            o = urlparse(web._getNormalizedURL(url), "http")

            # Skip short URLs
            if (o.netloc == "" or o.netloc in PROVIDERS or
                    len(o.netloc) + len(o.path) < 17):
                continue

            for recv in msg.to:
                if recv not in LAST_URLS:
                    LAST_URLS[recv] = list()
                LAST_URLS[recv].append(url)
    return msg


# MODULE INTERFACE ####################################################

@hook.command("framalink",
      help="Reduce any long URL",
      help_usage={
          None: "Reduce the last URL said on the channel",
          "URL [URL ...]": "Reduce the given URL(s)"
      },
      keywords={
          "provider=SMTH": "Change the service provider used (by default: %s) among %s" % (DEFAULT_PROVIDER, ", ".join(PROVIDERS.keys()))
      })
def cmd_reduceurl(msg):
    minify = list()

    if not len(msg.args):
        global LAST_URLS
        if msg.channel in LAST_URLS and len(LAST_URLS[msg.channel]) > 0:
            minify.append(LAST_URLS[msg.channel].pop())
        else:
            raise IMException("I have no more URL to reduce.")

    if len(msg.args) > 4:
        raise IMException("I cannot reduce that many URLs at once.")
    else:
        minify += msg.args

    if 'provider' in msg.kwargs and msg.kwargs['provider'] in PROVIDERS:
        provider = msg.kwargs['provider']
    else:
        provider = DEFAULT_PROVIDER

    res = list()
    for url in minify:
        o = urlparse(web.getNormalizedURL(url), "http")
        minief_url = reduce(url, provider)
        if o.netloc == "":
            res.append(gen_response(minief_url, msg, o.scheme))
        else:
            res.append(gen_response(minief_url, msg, o.netloc))
    return res
