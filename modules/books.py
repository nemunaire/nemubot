"""Looking for books"""

# PYTHON STUFFS #######################################################

import urllib

from nemubot import context
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response


# LOADING #############################################################

def load(context):
    if not context.config or not context.config.getAttribute("goodreadskey"):
        raise ImportError("You need a Goodreads API key in order to use this "
                          "module. Add it to the module configuration file:\n"
                          "<module name=\"books\" goodreadskey=\"XXXXXX\" />\n"
                          "Get one at https://www.goodreads.com/api/keys")


# MODULE CORE #########################################################

def get_book(title):
    """Retrieve a book from its title"""
    response = web.getXML("https://www.goodreads.com/book/title.xml?key=%s&title=%s" %
                          (context.config["goodreadskey"], urllib.parse.quote(title)))
    if response is not None and response.hasNode("book"):
        return response.getNode("book")
    else:
        return None


def search_books(title):
    """Get a list of book matching given title"""
    response = web.getXML("https://www.goodreads.com/search.xml?key=%s&q=%s" %
                          (context.config["goodreadskey"], urllib.parse.quote(title)))
    if response is not None and response.hasNode("search"):
        return response.getNode("search").getNode("results").getNodes("work")
    else:
        return []


def search_author(name):
    """Looking for an author"""
    response = web.getXML("https://www.goodreads.com/api/author_url/%s?key=%s" %
                          (urllib.parse.quote(name), context.config["goodreadskey"]))
    if response is not None and response.hasNode("author") and response.getNode("author").hasAttribute("id"):
        response = web.getXML("https://www.goodreads.com/author/show/%s.xml?key=%s" %
                              (urllib.parse.quote(response.getNode("author")["id"]), context.config["goodreadskey"]))
        if response is not None and response.hasNode("author"):
            return response.getNode("author")
    return None


# MODULE INTERFACE ####################################################

@hook("cmd_hook", "book",
      help="Get information about a book from its title",
      help_usage={
          "TITLE": "Get information about a book titled TITLE"
      })
def cmd_book(msg):
    if not len(msg.args):
        raise IRCException("please give me a title to search")

    book = get_book(" ".join(msg.args))
    if book is None:
        raise IRCException("unable to find book named like this")
    res = Response(channel=msg.channel)
    res.append_message("%s, writed by %s: %s" % (book.getNode("title").getContent(),
                                                 book.getNode("authors").getNode("author").getNode("name").getContent(),
                                                 web.striphtml(book.getNode("description").getContent())))
    return res


@hook("cmd_hook", "search_books",
      help="Search book's title",
      help_usage={
          "APPROX_TITLE": "Search for a book approximately titled APPROX_TITLE"
      })
def cmd_books(msg):
    if not len(msg.args):
        raise IRCException("please give me a title to search")

    title = " ".join(msg.args)
    res = Response(channel=msg.channel,
                   title="%s" % (title),
                   count=" (%d more books)")

    for book in search_books(title):
        res.append_message("%s, writed by %s" % (book.getNode("best_book").getNode("title").getContent(),
                                                 book.getNode("best_book").getNode("author").getNode("name").getContent()))
    return res


@hook("cmd_hook", "author_books",
      help="Looking for books writen by a given author",
      help_usage={
          "AUTHOR": "Looking for books writen by AUTHOR"
      })
def cmd_author(msg):
    if not len(msg.args):
        raise IRCException("please give me an author to search")

    ath = search_author(" ".join(msg.args))
    return Response([b.getNode("title").getContent() for b in ath.getNode("books").getNodes("book")],
                    channel=msg.channel,
                    title=ath.getNode("name").getContent())
