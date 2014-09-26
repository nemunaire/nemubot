# coding=utf-8

"""The weather module"""

import datetime
import json
import re
from urllib.parse import quote
from urllib.request import urlopen

from hooks import hook

import mapquest

nemubotversion = 3.4

from more import Response

def load(context):
    global DATAS
    DATAS.setIndex("name", "city")

    if not CONF or not CONF.hasNode("darkskyapi") or not CONF.getNode("darkskyapi").hasAttribute("key"):
        print ("You need a Dark-Sky API key in order to use this "
               "module. Add it to the module configuration file:\n<darkskyapi"
               " key=\"XXXXXXXXXXXXXXXX\" />\nRegister at "
               "http://developer.forecast.io/")
        return None

    from hooks.messagehook import MessageHook
    add_hook("cmd_hook", MessageHook(cmd_weather, "météo"))
    add_hook("cmd_hook", MessageHook(cmd_alert, "alert"))
    add_hook("cmd_hook", MessageHook(cmd_coordinates, "coordinates"))


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
    if len(msg.cmds) > 1:

        # catch dans X[jh]$
        if len(msg.cmds) > 3 and msg.cmds[len(msg.cmds) - 2] == "dans" or msg.cmds[len(msg.cmds) - 2] == "in" or msg.cmds[len(msg.cmds) - 2] == "next":
            specific = msg.cmds[len(msg.cmds) - 1]
            msg.cmds = msg.cmds[:len(msg.cmds) - 2]
        else:
            specific = None

        j = " ".join(msg.cmds[1:]).lower()

        if len(msg.cmds) == 3:
            coords = msg.cmds[1:3]
        else:
            coords = msg.cmds[1].split(",")

        try:
            if len(coords) == 2 and str(float(coords[0])) == coords[0] and str(float(coords[1])) == coords[1]:
                return coords, specific
        except ValueError:
            pass

        if j in DATAS.index:
            coords = list()
            coords.append(DATAS.index[j]["lat"])
            coords.append(DATAS.index[j]["long"])
            return j, coords, specific

        else:
            geocode = [x for x in mapquest.geocode(j)]
            if len(geocode):
                coords = list()
                coords.append(geocode[0]["latLng"]["lat"])
                coords.append(geocode[0]["latLng"]["lng"])
                return mapquest.where(geocode[0]), coords, specific

        raise IRCException("Je ne sais pas où se trouve %s." % " ".join(msg.cmds[1:]))

    else:
        raise IRCException("indique-moi un nom de ville ou des coordonnées.")


def get_json_weather(coords):
    raw = urlopen("https://api.forecast.io/forecast/%s/%s,%s" % (CONF.getNode("darkskyapi")["key"], float(coords[0]), float(coords[1])), timeout=10)
    wth = json.loads(raw.read().decode())

    # First read flags
    if "darksky-unavailable" in wth["flags"]:
        raise IRCException("The given location is supported but a temporary error (such as a radar station being down for maintenace) made data unavailable.")

    return wth


def cmd_coordinates(msg):
    if len(msg.cmds) <= 1:
        raise IRCException("indique-moi un nom de ville.")

    j = msg.cmds[1].lower()
    if j not in DATAS.index:
        raise IRCException("%s n'est pas une ville connue" % msg.cmds[1])

    coords = DATAS.index[j]
    return Response("Les coordonnées de %s sont %s,%s" % (msg.cmds[1], coords["lat"], coords["long"]), channel=msg.channel)

def cmd_alert(msg):
    loc, coords, specific = treat_coord(msg)
    wth = get_json_weather(coords)

    res = Response(channel=msg.channel, nomore="No more weather alert", count=" (%d more alerts)")

    if "alerts" in wth:
        for alert in wth["alerts"]:
            res.append_message("\x03\x02%s\x03\x02 (see %s expire on %s): %s" % (alert["title"], alert["uri"], format_timestamp(int(alert["expires"]), wth["timezone"], wth["offset"]), alert["description"].replace("\n", " ")))

    return res

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

        if city_name in DATAS.index:
            DATAS.index[city_name]["lat"] = gps_lat
            DATAS.index[city_name]["long"] = gps_long
        else:
            ms = ModuleState("city")
            ms.setAttribute("name", city_name)
            ms.setAttribute("lat", gps_lat)
            ms.setAttribute("long", gps_long)
            DATAS.addChild(ms)
        save()
        return Response("ok, j'ai bien noté les coordonnées de %s" % res.group("city"),
                        msg.channel, msg.nick)
