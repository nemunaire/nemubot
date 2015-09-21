from urllib.parse import urlparse
import re, json, subprocess

from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools.web import getURLContent
from more import Response

"""Get information of youtube videos"""

nemubotversion = 3.4

def help_full():
  return "!yt [<url>]: with an argument, get information about the given link; without arguments, use the latest link seen on the current channel."

def _get_ytdl(links):
  cmd = 'youtube-dl -j --'.split()
  cmd.extend(links)
  res = []
  with subprocess.Popen(cmd, stdout=subprocess.PIPE) as p:
    if p.wait() > 0:
      raise IRCException("Error while retrieving video information.")
    for line in p.stdout.read().split(b"\n"):
      localres = ''
      if not line:
        continue
      info = json.loads(line.decode('utf-8'))
      if info.get('fulltitle'):
        localres += info['fulltitle']
      elif info.get('title'):
        localres += info['title']
      else:
        continue
      if info.get('duration'):
        d = info['duration']
        localres += ' [{0}:{1:06.3f}]'.format(int(d/60), d%60)
      if info.get('age_limit'):
        localres += ' [-{}]'.format(info['age_limit'])
      if info.get('uploader'):
        localres += ' by {}'.format(info['uploader'])
      if info.get('upload_date'):
        localres += ' on {}'.format(info['upload_date'])
      if info.get('description'):
        localres += ': ' +  info['description']
      if info.get('webpage_url'):
        localres += ' | ' +  info['webpage_url']
      res.append(localres)
  if not res:
    raise IRCException("No video information to retrieve about this. Sorry!")
  return res

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

  data = _get_ytdl(links)
  res = Response(channel=msg.channel)
  for msg in data:
    res.append_message(msg)
  return res


@hook("msg_default")
def parselisten(msg):
    parseresponse(msg)
    return None


@hook("all_post")
def parseresponse(msg):
    global LAST_URLS
    if hasattr(msg, "text"):
      urls = re.findall("([a-zA-Z0-9+.-]+:(?://)?[^ ]+)", msg.text)
      for url in urls:
        o = urlparse(url)
        if o.scheme != "":
          if o.netloc == "" and len(o.path) < 10:
            continue
          for recv in msg.receivers:
            if recv not in LAST_URLS:
              LAST_URLS[recv] = list()
            LAST_URLS[recv].append(url)
    return msg
