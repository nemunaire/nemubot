"""Lost? use our commands to find your way!"""

# PYTHON STUFFS #######################################################

import re
import urllib.parse

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from nemubot.module.more import Response

# GLOBALS #############################################################

URL_DIRECTIONS_API = "https://api.openrouteservice.org/directions?api_key=%s&"
URL_GEOCODE_API = "https://api.openrouteservice.org/geocoding?api_key=%s&"

waytype = [
    "unknown",
    "state road",
    "road",
    "street",
    "path",
    "track",
    "cycleway",
    "footway",
    "steps",
    "ferry",
    "construction",
]


# LOADING #############################################################

def load(context):
    if not context.config or "apikey" not in context.config:
        raise ImportError("You need an OpenRouteService API key in order to use this "
                          "module. Add it to the module configuration file:\n"
                          "<module name=\"ors\" apikey=\"XXXXXXXXXXXXXXXX\" "
                          "/>\nRegister at https://developers.openrouteservice.org")
    global URL_DIRECTIONS_API
    URL_DIRECTIONS_API = URL_DIRECTIONS_API % context.config["apikey"]
    global URL_GEOCODE_API
    URL_GEOCODE_API = URL_GEOCODE_API % context.config["apikey"]


# MODULE CORE #########################################################

def approx_distance(lng):
    if lng > 1111:
        return "%f km" % (lng / 1000)
    else:
        return "%f m" % lng


def approx_duration(sec):
    days = int(sec / 86400)
    if days > 0:
        return "%d days %f hours" % (days, (sec % 86400) / 3600)
    hours = int((sec % 86400) / 3600)
    if hours > 0:
        return "%d hours %f minutes" % (hours, (sec % 3600) / 60)
    minutes = (sec % 3600) / 60
    if minutes > 0:
        return "%d minutes" % minutes
    else:
        return "%d seconds" % sec


def geocode(query, limit=7):
    obj = web.getJSON(URL_GEOCODE_API + urllib.parse.urlencode({
        'query': query,
        'limit': limit,
    }))

    for f in obj["features"]:
        yield f["geometry"]["coordinates"], f["properties"]


def firstgeocode(query):
    for g in geocode(query, limit=1):
        return g


def where(loc):
    return "{name} {city} {state} {county} {country}".format(**loc)


def directions(coordinates, **kwargs):
    kwargs['coordinates'] = '|'.join(coordinates)

    print(URL_DIRECTIONS_API + urllib.parse.urlencode(kwargs))
    return web.getJSON(URL_DIRECTIONS_API + urllib.parse.urlencode(kwargs), decode_error=True)


# MODULE INTERFACE ####################################################

@hook.command("geocode",
              help="Get GPS coordinates of a place",
              help_usage={
                  "PLACE": "Get GPS coordinates of PLACE"
              })
def cmd_geocode(msg):
    res = Response(channel=msg.channel, nick=msg.frm,
                   nomore="No more geocode", count=" (%s more geocode)")

    for loc in geocode(' '.join(msg.args)):
        res.append_message("%s is at %s,%s" % (
            where(loc[1]),
            loc[0][1], loc[0][0],
        ))

    return res


@hook.command("directions",
              help="Get routing instructions",
              help_usage={
                  "POINT1 POINT2 ...": "Get routing instructions to go from POINT1 to the last POINTX via intermediates POINTX"
              },
              keywords={
                  "profile=PROF": "One of driving-car, driving-hgv, cycling-regular, cycling-road, cycling-safe, cycling-mountain, cycling-tour, cycling-electric, foot-walking, foot-hiking, wheelchair. Default: foot-walking",
                  "preference=PREF": "One of fastest, shortest, recommended. Default: recommended",
                  "lang=LANG": "default: en",
              })
def cmd_directions(msg):
    drcts = directions(["{0},{1}".format(*firstgeocode(g)[0]) for g in msg.args],
                       profile=msg.kwargs["profile"] if "profile" in msg.kwargs else "foot-walking",
                       preference=msg.kwargs["preference"] if "preference" in msg.kwargs else "recommended",
                       units="m",
                       language=msg.kwargs["lang"] if "lang" in msg.kwargs else "en",
                       geometry=False,
                       instructions=True,
                       instruction_format="text")
    if "error" in drcts and "message" in drcts["error"] and drcts["error"]["message"]:
        raise IMException(drcts["error"]["message"])

    if "routes" not in drcts or not drcts["routes"]:
        raise IMException("No route available for this trip")

    myway = drcts["routes"][0]
    myway["summary"]["strduration"] = approx_duration(myway["summary"]["duration"])
    myway["summary"]["strdistance"] = approx_distance(myway["summary"]["distance"])
    res = Response("Trip summary: {strdistance} in approximate {strduration}; elevation +{ascent} m -{descent} m".format(**myway["summary"]), channel=msg.channel, count=" (%d more steps)", nomore="You have arrived!")

    def formatSegments(segments):
        for segment in segments:
            for step in segment["steps"]:
                step["strtype"] = waytype[step["type"]]
                step["strduration"] = approx_duration(step["duration"])
                step["strdistance"] = approx_distance(step["distance"])
                yield "{instruction} for {strdistance} on {strtype} (approximate time: {strduration})".format(**step)

    if "segments" in myway:
        res.append_message([m for m in formatSegments(myway["segments"])])

    return res
