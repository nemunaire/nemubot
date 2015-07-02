# coding=utf-8

"""The weather module"""

import datetime
import re
from urllib.parse import quote

from nemubot import context
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools import web
from nemubot.tools.xmlparser.node import ModuleState

import mapquest

nemubotversion = 4.0

from more import Response

URL_DSAPI = "https://api.forecast.io/forecast/%s/%%s,%%s"

def load(context):
    if not context.config or not context.config.hasAttribute("darkskyapikey"):
        raise ImportError("You need a Dark-Sky API key in order to use this "
                          "module. Add it to the module configuration file:\n"
                          "<module name=\"weather\" darkskyapikey=\"XXX\" />\n"
                          "Register at http://developer.forecast.io/")
    context.data.setIndex("name", "city")
    global URL_DSAPI
    URL_DSAPI = URL_DSAPI % context.config["darkskyapikey"]


def help_full ():
    return "!weather /city/: Display the current weather in /city/."


def fahrenheit2celsius(temp):
    return int((temp - 32) * 50/9)/10


def mph2kmph(speed):
    return int(speed * 160.9344)/100


def inh2mmh(size):
    return int(size * 254)/10


def format_wth(wth):
    return ("%s °C %s; precipitation (%s %% chance) intensity: %s mm/h; relative humidity: %s %%; wind speed: %s km/h %s°; cloud coverage: %s %%; pressure: %s hPa; ozone: %s DU" %
           (
               fahrenheit2celsius(wth["temperature"]),
               wth["summary"],
               int(wth["precipProbability"] * 100),
               inh2mmh(wth["precipIntensity"]),
               int(wth["humidity"] * 100),
               mph2kmph(wth["windSpeed"]),
               wth["windBearing"],
               int(wth["cloudCover"] * 100),
               int(wth["pressure"]),
               int(wth["ozone"])
           ))


def format_forecast_daily(wth):
    return ("%s; between %s-%s °C; precipitation (%s %% chance) intensity: maximum %s mm/h; relative humidity: %s %%; wind speed: %s km/h %s°; cloud coverage: %s %%; pressure: %s hPa; ozone: %s DU" %
           (
               wth["summary"],
               fahrenheit2celsius(wth["temperatureMin"]), fahrenheit2celsius(wth["temperatureMax"]),
               int(wth["precipProbability"] * 100),
               inh2mmh(wth["precipIntensityMax"]),
               int(wth["humidity"] * 100),
               mph2kmph(wth["windSpeed"]),
               wth["windBearing"],
               int(wth["cloudCover"] * 100),
               int(wth["pressure"]),
               int(wth["ozone"])
           ))


def format_timestamp(timestamp, tzname, tzoffset, format="%c"):
    tz = datetime.timezone(datetime.timedelta(hours=tzoffset), tzname)
    time = datetime.datetime.fromtimestamp(timestamp, tz=tz)
    return time.strftime(format)


def treat_coord(msg):
    if len(msg.args) > 0:

        # catch dans X[jh]$
        if len(msg.args) > 2 and (msg.args[-2] == "dans" or msg.args[-2] == "in" or msg.args[-2] == "next"):
            specific = msg.args[-1]
            city = " ".join(msg.args[:-2]).lower()
        else:
            specific = None
            city = " ".join(msg.args).lower()

        if len(msg.args) == 2:
            coords = msg.args
        else:
            coords = msg.args[0].split(",")

        try:
            if len(coords) == 2 and str(float(coords[0])) == coords[0] and str(float(coords[1])) == coords[1]:
                return coords, specific
        except ValueError:
            pass

        if city in context.data.index:
            coords = list()
            coords.append(context.data.index[city]["lat"])
            coords.append(context.data.index[city]["long"])
            return city, coords, specific

        else:
            geocode = [x for x in mapquest.geocode(city)]
            if len(geocode):
                coords = list()
                coords.append(geocode[0]["latLng"]["lat"])
                coords.append(geocode[0]["latLng"]["lng"])
                return mapquest.where(geocode[0]), coords, specific

        raise IRCException("Je ne sais pas où se trouve %s." % city)

    else:
        raise IRCException("indique-moi un nom de ville ou des coordonnées.")


def get_json_weather(coords):
    wth = web.getJSON(URL_DSAPI % (float(coords[0]), float(coords[1])))

    # First read flags
    if wth is None or "darksky-unavailable" in wth["flags"]:
        raise IRCException("The given location is supported but a temporary error (such as a radar station being down for maintenace) made data unavailable.")

    return wth


@hook("cmd_hook", "coordinates")
def cmd_coordinates(msg):
    if len(msg.args) < 1:
        raise IRCException("indique-moi un nom de ville.")

    j = msg.args[0].lower()
    if j not in context.data.index:
        raise IRCException("%s n'est pas une ville connue" % msg.args[0])

    coords = context.data.index[j]
    return Response("Les coordonnées de %s sont %s,%s" % (msg.args[0], coords["lat"], coords["long"]), channel=msg.channel)


@hook("cmd_hook", "alert")
def cmd_alert(msg):
    loc, coords, specific = treat_coord(msg)
    wth = get_json_weather(coords)

    res = Response(channel=msg.channel, nomore="No more weather alert", count=" (%d more alerts)")

    if "alerts" in wth:
        for alert in wth["alerts"]:
            res.append_message("\x03\x02%s\x03\x02 (see %s expire on %s): %s" % (alert["title"], alert["uri"], format_timestamp(int(alert["expires"]), wth["timezone"], wth["offset"]), alert["description"].replace("\n", " ")))

    return res


@hook("cmd_hook", "météo")
def cmd_weather(msg):
    loc, coords, specific = treat_coord(msg)
    wth = get_json_weather(coords)

    res = Response(channel=msg.channel, nomore="No more weather information")

    if "alerts" in wth:
        alert_msgs = list()
        for alert in wth["alerts"]:
            alert_msgs.append("\x03\x02%s\x03\x02 expire on %s" % (alert["title"], format_timestamp(int(alert["expires"]), wth["timezone"], wth["offset"])))
        res.append_message("\x03\x16\x03\x02/!\\\x03\x02 Alert%s:\x03\x16 " % ("s" if len(alert_msgs) > 1 else "") + ", ".join(alert_msgs))

    if specific is not None:
        gr = re.match(r"^([0-9]*)\s*([a-zA-Z])", specific)
        if gr is None or gr.group(1) == "":
            gr1 = 1
        else:
            gr1 = int(gr.group(1))

        if gr.group(2).lower() == "h" and gr1 < len(wth["hourly"]["data"]):
            hour = wth["hourly"]["data"][gr1]
            res.append_message("\x03\x02At %sh:\x03\x02 %s" % (format_timestamp(int(hour["time"]), wth["timezone"], wth["offset"], '%H'), format_wth(hour)))

        elif gr.group(2).lower() == "d" and gr1 < len(wth["daily"]["data"]):
            day = wth["daily"]["data"][gr1]
            res.append_message("\x03\x02On %s:\x03\x02 %s" % (format_timestamp(int(day["time"]), wth["timezone"], wth["offset"], '%A'), format_forecast_daily(day)))

        else:
            res.append_message("I don't understand %s or information is not available" % specific)

    else:
        res.append_message("\x03\x02Currently:\x03\x02 " + format_wth(wth["currently"]))

        nextres = "\x03\x02Today:\x03\x02 %s " % wth["daily"]["data"][0]["summary"]
        if "minutely" in wth:
            nextres += "\x03\x02Next hour:\x03\x02 %s " % wth["minutely"]["summary"]
        nextres += "\x03\x02Next 24 hours:\x03\x02 %s \x03\x02Next week:\x03\x02 %s" % (wth["hourly"]["summary"], wth["daily"]["summary"])
        res.append_message(nextres)

        for hour in wth["hourly"]["data"][1:4]:
            res.append_message("\x03\x02At %sh:\x03\x02 %s" % (format_timestamp(int(hour["time"]), wth["timezone"], wth["offset"], '%H'),
                                                               format_wth(hour)))

        for day in wth["daily"]["data"][1:]:
            res.append_message("\x03\x02On %s:\x03\x02 %s" % (format_timestamp(int(day["time"]), wth["timezone"], wth["offset"], '%A'),
                                                              format_forecast_daily(day)))

    return res


gps_ask = re.compile(r"^\s*(?P<city>.*\w)\s*(?:(?:se|est)\s+(?:trouve|situ[ée]*)\s+[aà])\s*(?P<lat>-?[0-9]+(?:[,.][0-9]+))[^0-9.](?P<long>-?[0-9]+(?:[,.][0-9]+))\s*$", re.IGNORECASE)


@hook("ask_default")
def parseask(msg):
    res = gps_ask.match(msg.text)
    if res is not None:
        city_name = res.group("city").lower()
        gps_lat = res.group("lat").replace(",", ".")
        gps_long = res.group("long").replace(",", ".")

        if city_name in context.data.index:
            context.data.index[city_name]["lat"] = gps_lat
            context.data.index[city_name]["long"] = gps_long
        else:
            ms = ModuleState("city")
            ms.setAttribute("name", city_name)
            ms.setAttribute("lat", gps_lat)
            ms.setAttribute("long", gps_long)
            context.data.addChild(ms)
        context.save()
        return Response("ok, j'ai bien noté les coordonnées de %s" % res.group("city"),
                        msg.channel, msg.nick)
