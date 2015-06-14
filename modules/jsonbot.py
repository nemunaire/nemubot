from bs4 import BeautifulSoup

from nemubot.hooks import hook
from nemubot.exception import IRCException
from nemubot.tools import web
from more import Response
import json

nemubotversion = 3.4

def help_full():
    return "Retrieves data from json"


@hook("cmd_hook", "json")
def get_hn_info(msg):
    if len(msg.cmds) < 2:
      raise IRCException("Please specify a url and a list of JSON keys.")

    request_data = web.getURLContent(msg.cmds[1])
    if not request_data:
      raise IRCException("Please specify a valid url.")
    json_data = json.loads(request_data)

    if len(msg.cmds) == 2:
      raise IRCException("Please specify the keys to return (%s)" % ", ".join(json_data.keys()))

    tags = msg.cmds[2].split(',')
    response = ""
    for tag in tags:
      if not tag in json_data.keys():
        raise IRCException("The key '%s' was not found in the JSON retrieved." % tag)
      response += tag + ": " + str(json_data[tag]) + "\n"

    return Response(response, channel=msg.channel, nomore="No more content", count=" (%d more lines)")
