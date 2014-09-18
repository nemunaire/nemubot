# coding=utf-8

import json
import re
from urllib.parse import quote
from urllib.request import urlopen

nemubotversion = 3.4

def load(context):
    if not CONF or not CONF.hasNode("mapquestapi") or not CONF.getNode("mapquestapi").hasAttribute("key"):
        print ("You need a MapQuest API key in order to use this "
               "module. Add it to the module configuration file:\n<mapquestapi"
               " key=\"XXXXXXXXXXXXXXXX\" />\nRegister at "
               "http://developer.mapquest.com/")
        return None

    from hooks.messagehook import MessageHook
    add_hook("cmd_hook", MessageHook(cmd_geocode, "geocode"))


def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "The mapquest module"

def help_full ():
    return "!geocode /place/: get coordinate of /place/."


def geocode(location):
    raw = urlopen("http://open.mapquestapi.com/geocoding/v1/address?key=%s&location=%s" % (CONF.getNode("mapquestapi")["key"], quote(location)))
    obj = json.loads(raw.read().decode())

    if "results" in obj and "locations" in obj["results"][0]:
        for loc in obj["results"][0]["locations"]:
            yield loc

def where(loc):
    return re.sub(" +", " ", "%s %s %s %s %s" % (loc["street"], loc["adminArea5"], loc["adminArea4"], loc["adminArea3"], loc["adminArea1"])).strip()

def cmd_geocode(msg):
    if len(msg.cmds) < 2:
        raise IRCException("indicate a name")

    locname = ' '.join(msg.cmds[1:])
    res = Response(channel=msg.channel, nick=msg.nick, nomore="No more geocode", count=" (%s more geocode)")
    for loc in geocode(locname):
        res.append_message("%s is at %s,%s (%s precision)" % (where(loc), loc["latLng"]["lat"], loc["latLng"]["lng"], loc["geocodeQuality"].lower()))
    return res
