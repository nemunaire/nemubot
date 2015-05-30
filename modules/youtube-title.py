import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools.web import getURLContent
from more import Response

"""Get information of youtube videos"""

nemubotversion = 3.4

def help_full():
  return "!yt [<url>]: with an argument, get information about the given link; without arguments, use the latest youtube link seen on the current channel."

LAST_URLS = dict()

@hook("cmd_hook", "yt")
def get_info_yt(msg):
  links = list()

  if len(msg.args) <= 0:
    global LAST_URLS
    if msg.channel in LAST_URLS and len(LAST_URLS[msg.channel]) > 0:
      links.append(LAST_URLS[msg.channel].pop())
    else:
      raise IRCException("I don't have any youtube URL for now, please provide me one to get information!")
  else:
    for url in msg.args:
      links.append(url)

  titles = list()
  descrip = list()
  for url in links:
    if not re.findall("([a-zA-Z0-9+.-]+:(?://)?[^ ]+)", url):
      url = "http://youtube.com/watch?v=" + url
    soup = BeautifulSoup(getURLContent(url))
    shortlink = soup.head.find("link", rel="shortlink")
    titl = soup.body.find(id='eow-title')
    titles.append("%s : %s" % (shortlink["href"], titl.text.strip()))
    desc = soup.body.find(id='eow-description')
    descrip.append(desc.text.strip())
  res = Response(channel=msg.channel)
  if len(titles) > 0:
    res.append_message(titles)
    for d in descrip:
      res.append_message(d)
  return res


@hook("msg_default")
def parselisten(msg):
    parseresponse(msg)
    return None


@hook("all_post")
def parseresponse(msg):
    global LAST_URLS
    urls = re.findall("([a-zA-Z0-9+.-]+:(?://)?[^ ]+)", msg.text)
    for url in urls:
      o = urlparse(url)
      if o.scheme != "":
        if o.netloc == "" and len(o.path) < 10:
          continue
        if (o.netloc == "youtube.com" or o.netloc == "www.youtube.com" or
            o.netloc == "youtu.be" or o.netloc == "www.youtu.be"):
          if msg.channel not in LAST_URLS:
            LAST_URLS[msg.channel] = list()
          LAST_URLS[msg.channel].append(url)
    return msg
