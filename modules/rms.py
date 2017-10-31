"""Finding RMS"""

# PYTHON STUFFS #######################################################

from bs4 import BeautifulSoup

from nemubot.hooks import hook
from nemubot.tools.web import getURLContent, striphtml
from nemubot.module.more import Response


# GLOBALS #############################################################

URL = 'https://www.fsf.org/events/rms-speeches.html'


# MODULE INTERFACE ####################################################

@hook.command("rms",
      help="Lists upcoming RMS events.")
def cmd_rms(msg):
    soup = BeautifulSoup(getURLContent(URL), "lxml")

    res = Response(channel=msg.channel,
                   nomore="",
                   count=" (%d more event(s))")

    search_res = soup.find("table", {'class':'listing'})
    for item in search_res.tbody.find_all('tr'):
        columns = item.find_all('td')
        res.append_message("RMS will be in \x02%s\x0F for \x02%s\x0F on \x02%s\x0F." % (
            columns[1].get_text(),
            columns[2].get_text().replace('\n', ''),
            columns[0].get_text().replace('\n', '')))
    return res
