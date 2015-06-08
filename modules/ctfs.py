from bs4 import BeautifulSoup

from nemubot.hooks import hook
from nemubot.tools.web import getURLContent
from more import Response

"""List upcoming CTFs"""

nemubotversion = 4.0

@hook("cmd_hook", "ctfs")
def get_info_yt(msg):
  soup = BeautifulSoup(getURLContent('https://ctftime.org/event/list/upcoming'))
  res = Response(channel=msg.channel, nomore="No more upcoming CTF")
  for line in soup.body.find_all('tr'):
    n = line.find_all('td')
    if len(n) == 5:
      try:
        res.append_message("\x02%s:\x0F from %s type %s at %s. %s" % tuple([x.text.replace("\n", " ").strip() for x in n]))
      except:
        import sys
        import traceback
        exc_type, exc_value, _ = sys.exc_info()
        sys.stderr.write(traceback.format_exception_only(exc_type, exc_value)[0])
  return res
