"""Show many information about a movie or serie"""

# PYTHON STUFFS #######################################################

import re
import urllib.parse

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response


# MODULE CORE #########################################################

def get_movie(title=None, year=None, imdbid=None, fullplot=True, tomatoes=False):
    """Returns the information about the matching movie"""

    # Built URL
    url = "http://www.omdbapi.com/?"
    if title is not None:
        url += "t=%s&" % urllib.parse.quote(title)
    if year is not None:
        url += "y=%s&" % urllib.parse.quote(year)
    if imdbid is not None:
        url += "i=%s&" % urllib.parse.quote(imdbid)
    if fullplot:
        url += "plot=full&"
    if tomatoes:
        url += "tomatoes=true&"

    # Make the request
    data = web.getJSON(url)

    # Return data
    if "Error" in data:
        raise IMException(data["Error"])

    elif "Response" in data and data["Response"] == "True":
        return data

    else:
        raise IMException("An error occurs during movie search")


def find_movies(title):
    """Find existing movies matching a approximate title"""

    # Built URL
    url = "http://www.omdbapi.com/?s=%s" % urllib.parse.quote(title)

    # Make the request
    data = web.getJSON(url)

    # Return data
    if "Error" in data:
        raise IMException(data["Error"])

    elif "Search" in data:
        return data

    else:
        raise IMException("An error occurs during movie search")


# MODULE INTERFACE ####################################################

@hook.command("imdb",
              help="View movie/serie details, using OMDB",
              help_usage={
                  "TITLE": "Look for a movie titled TITLE",
                  "IMDB_ID": "Look for the movie with the given IMDB_ID",
              })
def cmd_imdb(msg):
    if not len(msg.args):
        raise IMException("precise a movie/serie title!")

    title = ' '.join(msg.args)

    if re.match("^tt[0-9]{7}$", title) is not None:
        data = get_movie(imdbid=title)
    else:
        rm = re.match(r"^(.+)\s\(([0-9]{4})\)$", title)
        if rm is not None:
            data = get_movie(title=rm.group(1), year=rm.group(2))
        else:
            data = get_movie(title=title)

    res = Response(channel=msg.channel,
                   title="%s (%s)" % (data['Title'], data['Year']),
                   nomore="No more information, more at http://www.imdb.com/title/%s" % data['imdbID'])

    res.append_message("\x02rating\x0F: %s (%s votes); \x02plot\x0F: %s" %
                       (data['imdbRating'], data['imdbVotes'], data['Plot']))

    res.append_message("%s \x02from\x0F %s \x02released on\x0F %s; \x02genre:\x0F %s; \x02directed by:\x0F %s; \x02written by:\x0F %s; \x02main actors:\x0F %s"
                       % (data['Type'], data['Country'], data['Released'], data['Genre'], data['Director'], data['Writer'], data['Actors']))
    return res


@hook.command("imdbs",
              help="Search a movie/serie by title",
              help_usage={
                  "TITLE": "Search a movie/serie by TITLE",
              })
def cmd_search(msg):
    if not len(msg.args):
        raise IMException("precise a movie/serie title!")

    data = find_movies(' '.join(msg.args))

    movies = list()
    for m in data['Search']:
        movies.append("\x02%s\x0F (%s of %s)" % (m['Title'], m['Type'], m['Year']))

    return Response(movies, title="Titles found", channel=msg.channel)
