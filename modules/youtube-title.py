import urllib.request
from bs4 import BeautifulSoup
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools.web import getURLContent
from more import Response

nemubotversion = 3.4

def help_tiny():
  return "Return the video title from a youtube link"

def help_full():
  return "No help "

@hook("cmd_hook", "yt")
def get_info_yt(msg):
  if len(msg.args) <= 0:
    raise IRCException("Please provide an URL from youtube.com")

  res = list()
  for url in msg.args:
    req = getURLContent(url)
    soup = BeautifulSoup(req)
    desc = soup.body.find(id='eow-title')
    res.append(desc.text.strip())
  return Response(res, channel=msg.channel, nomore="No more description")
