# coding=utf-8

"""Transform name location to GPS coordinates"""

import re
from urllib.parse import quote

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

nemubotversion = 4.0

from more import Response

URL_API = "http://open.mapquestapi.com/geocoding/v1/address?key=%s&location=%%s"

def load(context):
    if not context.config or "apikey" not in context.config:
        raise ImportError("You need a MapQuest API key in order to use this "
                          "module. Add it to the module configuration file:\n"
                          "<module name=\"mapquest\" key=\"XXXXXXXXXXXXXXXX\" "
                          "/>\nRegister at http://developer.mapquest.com/")
    global URL_API
    URL_API = URL_API % context.config["apikey"].replace("%", "%%")


def help_full():
    return "!geocode /place/: get coordinate of /place/."


def geocode(location):
    obj = web.getJSON(URL_API % quote(location))

    if "results" in obj and "locations" in obj["results"][0]:
        for loc in obj["results"][0]["locations"]:
            yield loc


def where(loc):
    return re.sub(" +", " ",
                  "{street} {adminArea5} {adminArea4} {adminArea3} "
                  "{adminArea1}".format(**loc)).strip()


@hook("cmd_hook", "geocode")
def cmd_geocode(msg):
    if not len(msg.args):
        raise IMException("indicate a name")

    res = Response(channel=msg.channel, nick=msg.nick,
                   nomore="No more geocode", count=" (%s more geocode)")

    for loc in geocode(' '.join(msg.args)):
        res.append_message("%s is at %s,%s (%s precision)" %
                           (where(loc),
                            loc["latLng"]["lat"],
                            loc["latLng"]["lng"],
                            loc["geocodeQuality"].lower()))

    return res
