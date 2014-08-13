# coding=utf-8

import re

from tools import web

nemubotversion = 3.4

def load(context):
    global DATAS
    DATAS.setIndex("name", "station")

#  evt = ModuleEvent(station_available, "42706",
#                    (lambda a, b: a != b), None, 60,
#                    station_status)
#  context.add_event(evt)

def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "Gets information about velib stations"

def help_full ():
    return "!velib /number/ ...: gives available bikes and slots at the station /number/."


def station_status(station):
    """Gets available and free status of a given station"""
    response = web.getXML(CONF.getNode("server")["url"] + station)
    if response is not None:
        available = response.getNode("available").getContent()
        if available is not None and len(available) > 0:
            available = int(available)
        else:
            available = 0
        free = response.getNode("free").getContent()
        if free is not None and len(free) > 0:
            free = int(free)
        else:
            free = 0
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
        return Response(msg.sender,
                        "à la station %s : %d vélib et %d points d'attache"
                        " disponibles." % (station, available, free),
                        channel=msg.channel, nick=msg.nick)
    raise IRCException("station %s inconnue." % station)

def ask_stations(msg):
    """Hook entry from !velib"""
    global DATAS
    if len(msg.cmds) > 5:
        raise IRCException("demande-moi moins de stations à la fois.")

    elif len(msg.cmds) > 1:
        for station in msg.cmds[1:]:
            if re.match("^[0-9]{4,5}$", station):
                return print_station_status(msg, station)
            elif station in DATAS.index:
                return print_station_status(msg, DATAS.index[station]["number"])
            else:
                raise IRCException("numéro de station invalide.")

    else:
        raise IRCException("pour quelle station ?")
