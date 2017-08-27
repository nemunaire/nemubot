from datetime import datetime
import urllib

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import human
from nemubot.tools.web import getJSON

nemubotversion = 4.0

from nemubot.module.more import Response

URL_TPBAPI = None

def load(context):
    if not context.config or "url" not in context.config:
        raise ImportError("You need a TPB API in order to use the !tpb feature"
                          ". Add it to the module configuration file:\n<module"
                          "name=\"tpb\" url=\"http://tpbapi.org/\" />\nSample "
                          "API: "
                          "https://gist.github.com/colona/07a925f183cfb47d5f20")
    global URL_TPBAPI
    URL_TPBAPI = context.config["url"]

@hook.command("tpb")
def cmd_tpb(msg):
    if not len(msg.args):
        raise IMException("indicate an item to search!")

    torrents = getJSON(URL_TPBAPI + urllib.parse.quote(" ".join(msg.args)))

    res = Response(channel=msg.channel, nomore="No more torrents", count=" (%d more torrents)")

    if torrents:
        for t in torrents:
            t["sizeH"] = human.size(t["size"])
            t["dateH"] = datetime.fromtimestamp(t["date"]).strftime('%Y-%m-%d %H:%M:%S')
            res.append_message("\x03\x02{title}\x03\x02 in {category}, {sizeH}; added at {dateH}; id: {id}; magnet:?xt=urn:btih:{magnet}&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Fopen.demonii.com%3A1337".format(**t))

    return res
