"""List upcoming CTFs"""

# PYTHON STUFFS #######################################################

from bs4 import BeautifulSoup

from nemubot.hooks import hook
from nemubot.tools.web import getURLContent, striphtml
from nemubot.module.more import Response


# GLOBALS #############################################################

URL = 'https://ctftime.org/event/list/upcoming'


# MODULE INTERFACE ####################################################

@hook.command("ctfs",
      help="Display the upcoming CTFs")
def get_info_yt(msg):
    soup = BeautifulSoup(getURLContent(URL))

    res = Response(channel=msg.channel, nomore="No more upcoming CTF")

    for line in soup.body.find_all('tr'):
        n = line.find_all('td')
        if len(n) == 7:
            res.append_message("\x02%s:\x0F from %s type %s at %s. Weight: %s. %s%s" %
                               tuple([striphtml(x.text).strip() for x in n]))

    return res
