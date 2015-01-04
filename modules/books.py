# coding=utf-8

"""Looking for books"""

import urllib

from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools import web

nemubotversion = 3.4

from more import Response


def load(context):
    if not CONF or not CONF.hasNode("goodreadsapi") or not CONF.getNode("goodreadsapi").hasAttribute("key"):
        print ("You need a Goodreads API key in order to use this "
               "module. Add it to the module configuration file:\n<goodreadsapi"
               " key=\"XXXXXXXXXXXXXXXX\" />\nGet one at "
               "https://www.goodreads.com/api/keys")
        return None


def get_book(title):
    """Retrieve a book from its title"""
    response = web.getXML("https://www.goodreads.com/book/title.xml?key=%s&title=%s" %
                          (CONF.getNode("goodreadsapi")["key"], urllib.parse.quote(title)))
    if response is not None and response.hasNode("book"):
        return response.getNode("book")
    else:
        return None


def search_books(title):
    """Get a list of book matching given title"""
    response = web.getXML("https://www.goodreads.com/search.xml?key=%s&q=%s" %
                          (CONF.getNode("goodreadsapi")["key"], urllib.parse.quote(title)))
    if response is not None and response.hasNode("search"):
        return response.getNode("search").getNode("results").getNodes("work")
    else:
        return []


def search_author(name):
    """Looking for an author"""
    response = web.getXML("https://www.goodreads.com/api/author_url/%s?key=%s" %
                          (urllib.parse.quote(name), CONF.getNode("goodreadsapi")["key"]))
    if response is not None and response.hasNode("author") and response.getNode("author").hasAttribute("id"):
        response = web.getXML("https://www.goodreads.com/author/show/%s.xml?key=%s" %
                              (urllib.parse.quote(response.getNode("author")["id"]), CONF.getNode("goodreadsapi")["key"]))
        if response is not None and response.hasNode("author"):
            return response.getNode("author")
    return None


@hook("cmd_hook", "book")
def cmd_book(msg):
    if len(msg.cmds) < 2:
        raise IRCException("please give me a title to search")

    book = get_book(" ".join(msg.cmds[1:]))
    if book is None:
        raise IRCException("unable to find book named like this")
    res = Response(channel=msg.channel)
    res.append_message("%s, writed by %s: %s" % (book.getNode("title").getContent(),
                                                 book.getNode("authors").getNode("author").getNode("name").getContent(),
                                                 web.striphtml(book.getNode("description").getContent())))
    return res


@hook("cmd_hook", "search_books")
def cmd_books(msg):
    if len(msg.cmds) < 2:
        raise IRCException("please give me a title to search")

    title = " ".join(msg.cmds[1:])
    res = Response(channel=msg.channel,
                   title="%s" % (title),
                   count=" (%d more books)")

    for book in search_books(title):
        res.append_message("%s, writed by %s" % (book.getNode("best_book").getNode("title").getContent(),
                                                 book.getNode("best_book").getNode("author").getNode("name").getContent()))
    return res


@hook("cmd_hook", "author_books")
def cmd_author(msg):
    if len(msg.cmds) < 2:
        raise IRCException("please give me an author to search")

    ath = search_author(" ".join(msg.cmds[1:]))
    return Response([b.getNode("title").getContent() for b in ath.getNode("books").getNodes("book")],
                    channel=msg.channel,
                    title=ath.getNode("name").getContent())
