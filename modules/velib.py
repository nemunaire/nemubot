"""Gets information about velib stations"""

# PYTHON STUFFS #######################################################

import re

from nemubot import context
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response


# LOADING #############################################################

URL_API = None # http://www.velib.paris.fr/service/stationdetails/paris/%s

def load(context):
    global URL_API
    if not context.config or not context.config.hasAttribute("url"):
        raise ImportError("Please provide url attribute in the module configuration")
    URL_API = context.config["url"]
    context.data.setIndex("name", "station")

#  evt = ModuleEvent(station_available, "42706",
#                    (lambda a, b: a != b), None, 60,
#                    station_status)
#  context.add_event(evt)


# MODULE CORE #########################################################

def station_status(station):
    """Gets available and free status of a given station"""
    response = web.getXML(URL_API % station)
    if response is not None:
        available = int(response.getElementsByTagName("available")[0].firstChild.nodeValue)
        free = int(response.getElementsByTagName("free")[0].firstChild.nodeValue)
        return (available, free)
    else:
        return (None, None)


def station_available(station):
    """Gets available velib at a given velib station"""
    (a, f) = station_status(station)
    return a


def station_free(station):
    """Gets free slots at a given velib station"""
    (a, f) = station_status(station)
    return f


def print_station_status(msg, station):
    """Send message with information about the given station"""
    (available, free) = station_status(station)
    if available is not None and free is not None:
        return Response("À la station %s : %d vélib et %d points d'attache"
                        " disponibles." % (station, available, free),
                        channel=msg.channel)
    raise IRCException("station %s inconnue." % station)


# MODULE INTERFACE ####################################################

@hook("cmd_hook", "velib",
      help="gives available bikes and slots at the given station",
      help_usage={
          "STATION_ID": "gives available bikes and slots at the station STATION_ID"
      })
def ask_stations(msg):
    if len(msg.args) > 4:
        raise IRCException("demande-moi moins de stations à la fois.")
    elif not len(msg.args):
        raise IRCException("pour quelle station ?")

    for station in msg.args:
        if re.match("^[0-9]{4,5}$", station):
            return print_station_status(msg, station)
        elif station in context.data.index:
            return print_station_status(msg,
                                        context.data.index[station]["number"])
        else:
            raise IRCException("numéro de station invalide.")
