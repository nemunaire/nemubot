import urllib.request
from bs4 import BeautifulSoup
import pprint
from nemubot.hooks import hook
from more import Response

nemubotversion = 3.4

def help_tiny():
  return "CVE description"

def help_full():
  return "No help "


@hook("cmd_hook", "cve")
def get_cve_desc(msg):
  DESC_INDEX = 17
  BASEURL_MITRE = 'http://cve.mitre.org/cgi-bin/cvename.cgi?name='

  cve_id = ''

  if msg.cmds[1][:3] == 'cve' :
    cve_id = msg.cmds[1]

  else:
    cve_id = 'cve-' + msg.cmds[1]

  search_url = BASEURL_MITRE + cve_id.upper()

  url = urllib.request.urlopen(search_url)
  soup = BeautifulSoup(url)

  desc = soup.body.findAll('td')

  return Response(desc[DESC_INDEX].text, msg.channel)
