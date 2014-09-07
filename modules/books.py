# coding=utf-8

"""Looking for books"""

import urllib.request

from hooks import hook
from tools import web

nemubotversion = 3.4

def load(context):
    if not CONF or not CONF.hasNode("goodreadsapi") or not CONF.getNode("goodreadsapi").hasAttribute("key"):
        print ("You need a Goodreads API key in order to use this "
               "module. Add it to the module configuration file:\n<goodreadsapi"
               " key=\"XXXXXXXXXXXXXXXX\" />\nGet one at "
               "https://www.goodreads.com/api/keys")
        return None

def search_book(title):
    response = web.getXML("https://www.goodreads.com/search.xml?key=%s&q=%s" % (CONF.getNode("goodreadsapi")["key"], urllib.parse.quote(title)))
    if response is not None:
        return response.getNode("search").getNode("results").getNodes("work")
    else:
        return []

@hook("cmd_hook", "book")
def cmd_book(msg):
    if len(msg.cmds) < 2:
        raise IRCException("please give me a title to search")

    title = " ".join(msg.cmds)
    res = Response(msg.sender, channel=msg.channel,
                   title="%s" % (title), count=" (%d more books)")

    books = search_book(title)
    for book in books:
        res.append_message("%s, writed by %s" % (book.getNode("best_book").getNode("title").getContent(), book.getNode("best_book").getNode("author").getNode("name").getContent()))
    return res
