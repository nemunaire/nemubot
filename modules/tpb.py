import urllib

from tools.web import getJSON

nemubotversion = 3.4

from hooks import hook
from more import Response

URL_TPBAPI = None

def load(context):
    global URL_TPBAPI

    if not CONF or not CONF.hasNode("tpbapi") or not CONF.getNode("tpbapi").hasAttribute("url"):
        print ("You need a TPB API in order to use the !tpb feature. Add it to "
               "the module configuration file:\n"
               "<tpbapi url=\"http://tpbapi.org/\" />\nSample API: "
               "https://gist.github.com/colona/07a925f183cfb47d5f20")
    else:
        URL_TPBAPI = CONF.getNode("tpbapi")["url"]

        from hooks.messagehook import MessageHook
        add_hook("cmd_hook", MessageHook(cmd_tpb, "tpb"))


def cmd_tpb(msg):
    if len(msg.cmds) < 1:
        raise IRCException("indicate an item to search!")

    torrents = getJSON(URL_TPBAPI + urllib.parse.quote(" ".join(msg.cmds[1:])))

    res = Response(channel=msg.channel, nomore="No more torrents", count=" (%d more torrents)")

    if torrents:
        for t in torrents:
            res.append_message("\x03\x02{title}\x03\x02 in {category}, {size}B; id: {id}; magnet: {magnet}".format(**t))

    return res
