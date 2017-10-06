"""Search definition from urbandictionnary"""

# PYTHON STUFFS #######################################################

from urllib.parse import quote

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from nemubot.module.more import Response

# MODULE CORE #########################################################

def search(terms):
    return web.getJSON(
        "https://api.urbandictionary.com/v0/define?term=%s"
        % quote(' '.join(terms)))


# MODULE INTERFACE ####################################################

@hook.command("urbandictionnary")
def udsearch(msg):
    if not len(msg.args):
        raise IMException("Indicate a term to search")

    s = search(msg.args)

    res = Response(channel=msg.channel, nomore="No more results",
                   count=" (%d more definitions)")

    for i in s["list"]:
        res.append_message(i["definition"].replace("\n", "  "),
                           title=i["word"])

    return res
