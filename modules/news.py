"""Display latests news from a website"""

# PYTHON STUFFS #######################################################

import datetime
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response
from nemubot.tools.feed import Feed, AtomEntry


# HELP ################################################################

def help_full():
    return "Display the latests news from a given URL: !news URL"


# MODULE CORE #########################################################

def find_rss_links(url):
    soup = BeautifulSoup(web.getURLContent(url))
    for rss in soup.find_all('link', attrs={"type": re.compile("^application/(atom|rss)")}):
        yield urljoin(url, rss["href"])

def get_last_news(url):
    from xml.parsers.expat import ExpatError
    try:
        feed = Feed(web.getURLContent(url))
        return feed.entries
    except ExpatError:
        return []


# MODULE INTERFACE ####################################################

@hook("cmd_hook", "news")
def cmd_news(msg):
    if not len(msg.args):
        raise IRCException("Indicate the URL to visit.")

    url = " ".join(msg.args)
    links = [x for x in find_rss_links(url)]
    if len(links) == 0: links = [ url ]

    res = Response(channel=msg.channel, nomore="No more news from %s" % url)
    for n in get_last_news(links[0]):
        res.append_message("%s published %s: %s %s" % (("\x02" + web.striphtml(n.title) + "\x0F") if n.title else "An article without title",
                                                       (n.updated.strftime("on %A %d. %B %Y at %H:%M") if n.updated else "someday") if isinstance(n, AtomEntry) else n.pubDate,
                                                       web.striphtml(n.summary) if n.summary else "",
                                                       n.link if n.link else ""))
    return res
