"""Show many information about a movie or serie"""

# PYTHON STUFFS #######################################################

import re
import urllib.parse

from bs4 import BeautifulSoup

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response


# MODULE CORE #########################################################

def get_movie_by_id(imdbid):
    """Returns the information about the matching movie"""

    url = "http://www.imdb.com/title/" + urllib.parse.quote(imdbid)
    soup = BeautifulSoup(web.getURLContent(url))

    return {
        "imdbID": imdbid,
        "Title": soup.body.find(attrs={"itemprop": "name"}).next_element.strip(),
        "Year": soup.body.find(id="titleYear").find("a").text.strip() if soup.body.find(id="titleYear") else ", ".join([y.text.strip() for y in soup.body.find(attrs={"class": "seasons-and-year-nav"}).find_all("div")[3].find_all("a")[:-1]]),
        "Duration": soup.body.find_all(attrs={"itemprop": "duration"})[-1].text.strip(),
        "imdbRating": soup.body.find(attrs={"itemprop": "ratingValue"}).text.strip(),
        "imdbVotes": soup.body.find(attrs={"itemprop": "ratingCount"}).text.strip(),
        "Plot": re.sub(r"\s+", " ", soup.body.find(id="titleStoryLine").find(attrs={"itemprop": "description"}).text).strip(),

        "Type": "TV Series" if soup.find(attrs={"class": "np_episode_guide"}) else "Movie",
        "Country": ", ".join([c.find("a").text.strip() for c in soup.body.find(id="titleDetails").find_all(attrs={"class": "txt-block"}) if c.text.find("Country") != -1]),
        "Released": soup.body.find(attrs={"itemprop": "datePublished"}).attrs["content"] if "content" in soup.body.find(attrs={"itemprop": "datePublished"}).attrs else "N\A",
        "Genre": ", ".join([g.text.strip() for g in soup.body.find_all(attrs={"itemprop": "genre"})[:-1]]),
        "Director": ", ".join([d.find(attrs={"itemprop": "name"}).text.strip() for d in soup.body.find_all(attrs={"itemprop": "director"})]),
        "Writer": ", ".join([d.find(attrs={"itemprop": "name"}).text.strip() for d in soup.body.find_all(attrs={"itemprop": "creator"})]),
        "Actors": ", ".join([d.find(attrs={"itemprop": "name"}).text.strip() for d in soup.body.find_all(attrs={"itemprop": "actors"})]),
    }


def find_movies(title, year=None):
    """Find existing movies matching a approximate title"""

    title = title.lower()

    # Built URL
    url = "https://v2.sg.media-imdb.com/suggests/%s/%s.json" % (urllib.parse.quote(title[0]), urllib.parse.quote(title.replace(" ", "_")))

    # Make the request
    data = web.getJSON(url, remove_callback=True)

    if year is None:
        return data["d"]
    else:
        return [d for d in data["d"] if "y" in d and str(d["y"]) == year]


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
        data = get_movie_by_id(imdbid=title)
    else:
        rm = re.match(r"^(.+)\s\(([0-9]{4})\)$", title)
        if rm is not None:
            data = find_movies(rm.group(1), year=rm.group(2))
        else:
            data = find_movies(title)

        if not data:
            raise IMException("Movie/series not found")

        data = get_movie_by_id(data[0]["id"])

    res = Response(channel=msg.channel,
                   title="%s (%s)" % (data['Title'], data['Year']),
                   nomore="No more information, more at http://www.imdb.com/title/%s" % data['imdbID'])

    res.append_message("%s \x02genre:\x0F %s; \x02rating\x0F: %s (%s votes); \x02plot\x0F: %s" %
                       (data['Type'], data['Genre'], data['imdbRating'], data['imdbVotes'], data['Plot']))

    res.append_message("%s \x02from\x0F %s \x02released on\x0F %s; \x02directed by:\x0F %s; \x02written by:\x0F %s; \x02main actors:\x0F %s"
                       % (data['Type'], data['Country'], data['Released'], data['Director'], data['Writer'], data['Actors']))
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
    for m in data:
        movies.append("\x02%s\x0F%s with %s" % (m['l'], (" (" + str(m['y']) + ")") if "y" in m else "", m['s']))

    return Response(movies, title="Titles found", channel=msg.channel)
