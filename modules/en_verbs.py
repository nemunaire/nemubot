from bs4 import BeautifulSoup

from nemubot.hooks import hook
from nemubot.exception import IRCException
from nemubot.tools import web
from more import Response

nemubotversion = 3.4

def help_full():
    return "English irregular verbs help module"


@hook("cmd_hook", "english_irregular_verbs")
def get_irregular_verbs(msg):
    if len(msg.cmds) < 2:
        request_url = "http://irregular-verbs.23.tf/"
    else:
        request_url = ("http://irregular-verbs.23.tf/v/%s" % msg.cmds[1])

    request_data = web.getURLContent(request_url)

    return Response(request_data, channel=msg.channel, nomore="No more matching verbs", count="(%d more matching verbs)")

