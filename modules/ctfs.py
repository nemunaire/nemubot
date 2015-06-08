import urllib.request
from bs4 import BeautifulSoup
from hooks import hook
from more import Response

nemubotversion = 3.4

def help_tiny():
  return "No help"

def help_full():
  return "No help "

@hook("cmd_hook", "ctfs")
def get_info_yt(msg):
  req = urllib.request.Request('https://ctftime.org/event/list/upcoming',
                               data=None,
                               headers={
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
      })

  ctf = ''
  url = urllib.request.urlopen(req)
  soup = BeautifulSoup(url)
  desc = soup.body.find_all('td')
  i = 0
  for result in desc:
    ctf += result.text.replace('\n', ' ')
    ctf +=  ' '
    i += 1
    if not (i % 5):
      ctf += '\n'
  res = Response(channel=msg.channel, nomore="No more description")
  res.append_message(ctf)
  return res


