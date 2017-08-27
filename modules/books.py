"""Looking for books"""

# PYTHON STUFFS #######################################################

import urllib

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from nemubot.module.more import Response


# LOADING #############################################################

def load(context):
    if not context.config or "goodreadskey" not in context.config:
        raise ImportError("You need a Goodreads API key in order to use this "
                          "module. Add it to the module configuration file:\n"
                          "<module name=\"books\" goodreadskey=\"XXXXXX\" />\n"
                          "Get one at https://www.goodreads.com/api/keys")


# MODULE CORE #########################################################

def get_book(title):
    """Retrieve a book from its title"""
    response = web.getXML("https://www.goodreads.com/book/title.xml?key=%s&title=%s" %
                          (context.config["goodreadskey"], urllib.parse.quote(title)))
    if response is not None and len(response.getElementsByTagName("book")):
        return response.getElementsByTagName("book")[0]
    else:
        return None


def search_books(title):
    """Get a list of book matching given title"""
    response = web.getXML("https://www.goodreads.com/search.xml?key=%s&q=%s" %
                          (context.config["goodreadskey"], urllib.parse.quote(title)))
    if response is not None and len(response.getElementsByTagName("search")):
        return response.getElementsByTagName("search")[0].getElementsByTagName("results")[0].getElementsByTagName("work")
    else:
        return []


def search_author(name):
    """Looking for an author"""
    response = web.getXML("https://www.goodreads.com/api/author_url/%s?key=%s" %
                          (urllib.parse.quote(name), context.config["goodreadskey"]))
    if response is not None and len(response.getElementsByTagName("author")) and response.getElementsByTagName("author")[0].hasAttribute("id"):
        response = web.getXML("https://www.goodreads.com/author/show/%s.xml?key=%s" %
                              (urllib.parse.quote(response.getElementsByTagName("author")[0].getAttribute("id")), context.config["goodreadskey"]))
        if response is not None and len(response.getElementsByTagName("author")):
            return response.getElementsByTagName("author")[0]
    return None


# MODULE INTERFACE ####################################################

@hook.command("book",
      help="Get information about a book from its title",
      help_usage={
          "TITLE": "Get information about a book titled TITLE"
      })
def cmd_book(msg):
    if not len(msg.args):
        raise IMException("please give me a title to search")

    book = get_book(" ".join(msg.args))
    if book is None:
        raise IMException("unable to find book named like this")
    res = Response(channel=msg.channel)
    res.append_message("%s, written by %s: %s" % (book.getElementsByTagName("title")[0].firstChild.nodeValue,
                                                 book.getElementsByTagName("author")[0].getElementsByTagName("name")[0].firstChild.nodeValue,
                                                 web.striphtml(book.getElementsByTagName("description")[0].firstChild.nodeValue if book.getElementsByTagName("description")[0].firstChild else "")))
    return res


@hook.command("search_books",
      help="Search book's title",
      help_usage={
          "APPROX_TITLE": "Search for a book approximately titled APPROX_TITLE"
      })
def cmd_books(msg):
    if not len(msg.args):
        raise IMException("please give me a title to search")

    title = " ".join(msg.args)
    res = Response(channel=msg.channel,
                   title="%s" % (title),
                   count=" (%d more books)")

    for book in search_books(title):
        res.append_message("%s, writed by %s" % (book.getElementsByTagName("best_book")[0].getElementsByTagName("title")[0].firstChild.nodeValue,
                                                 book.getElementsByTagName("best_book")[0].getElementsByTagName("author")[0].getElementsByTagName("name")[0].firstChild.nodeValue))
    return res


@hook.command("author_books",
      help="Looking for books writen by a given author",
      help_usage={
          "AUTHOR": "Looking for books writen by AUTHOR"
      })
def cmd_author(msg):
    if not len(msg.args):
        raise IMException("please give me an author to search")

    name = " ".join(msg.args)
    ath = search_author(name)
    if ath is None:
        raise IMException("%s does not appear to be a published author." % name)
    return Response([b.getElementsByTagName("title")[0].firstChild.nodeValue for b in ath.getElementsByTagName("book")],
                    channel=msg.channel,
                    title=ath.getElementsByTagName("name")[0].firstChild.nodeValue)
