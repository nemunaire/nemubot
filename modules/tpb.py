from datetime import datetime
import urllib

from nemubot.hooks import hook
from nemubot.tools import human
from nemubot.tools.web import getJSON

nemubotversion = 3.4

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

        from nemubot.hooks.messagehook import MessageHook
        add_hook("cmd_hook", MessageHook(cmd_tpb, "tpb"))


def cmd_tpb(msg):
    if len(msg.cmds) < 1:
        raise IRCException("indicate an item to search!")

    torrents = getJSON(URL_TPBAPI + urllib.parse.quote(" ".join(msg.cmds[1:])))

    res = Response(channel=msg.channel, nomore="No more torrents", count=" (%d more torrents)")

    if torrents:
        for t in torrents:
            t["sizeH"] = human.size(t["size"])
            t["dateH"] = datetime.fromtimestamp(t["date"]).strftime('%Y-%m-%d %H:%M:%S')
            res.append_message("\x03\x02{title}\x03\x02 in {category}, {sizeH}; added at {dateH}; id: {id}; magnet:?xt=urn:btih:{magnet}&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Fopen.demonii.com%3A1337".format(**t))

    return res
