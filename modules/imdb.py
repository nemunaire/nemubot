# coding=utf-8

"""Show many information about a movie or serie"""

import json
import re
import urllib.request

from hooks import hook

nemubotversion = 3.4

def help_full ():
  return "Search a movie title with: !imdbs <approximative title> ; View movie details with !imdb <title>"

@hook("cmd_hook", "imdb", help="View movie details with !imdb <title>")
def cmd_imdb(msg):
    if len(msg.cmds) < 2:
        raise IRCException("precise a movie/serie title!")

    title = ' '.join(msg.cmds[1:])

    if re.match("^tt[0-9]{7}$", title) is not None:
        url = "http://www.omdbapi.com/?i=%s" % urllib.parse.quote(title)
    else:
        url = "http://www.omdbapi.com/?t=%s" % urllib.parse.quote(title)

    print_debug(url)

    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode())

    if "Error" in data:
        raise IRCException(data["Error"])

    elif "Response" in data and data["Response"] == "True":
        res =  Response(msg.sender, channel=msg.channel,
                        title="%s (%s)" % (data['Title'], data['Year']),
                        nomore="No more information, more at http://www.imdb.com/title/%s" % data['imdbID'])

        res.append_message("\x02rating\x0F: %s (%s votes); \x02plot\x0F: %s" %
                           (data['imdbRating'], data['imdbVotes'], data['Plot']))

        res.append_message("%s \x02from\x0F %s \x02released on\x0F %s; \x02genre:\x0F %s; \x02directed by:\x0F %s; \x02writed by:\x0F %s; \x02main actors:\x0F %s"
                           % (data['Type'], data['Country'], data['Released'], data['Genre'], data['Director'], data['Writer'], data['Actors']))
        return res

    else:
        raise IRCException("An error occurs during movie search")


@hook("cmd_hook", "imdbs", help="!imdbs <approximative title> to search a movie title")
def cmd_search(msg):
    url = "http://www.omdbapi.com/?s=%s" % urllib.parse.quote(' '.join(msg.cmds[1:]))
    print_debug(url)

    raw = urllib.request.urlopen(url)
    data = json.loads(raw.read().decode())

    if "Error" in data:
        raise IRCException(data["Error"])

    elif "Search" in data:
        movies = list()

        for m in data['Search']:
            movies.append("\x02%s\x0F (%s of %s)" % (m['Title'], m['Type'], m['Year']))

        return Response(msg.sender, movies, title="Titles found", channel=msg.channel)

    else:
        raise IRCException("An error occurs during movie search")
