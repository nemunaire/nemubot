# coding=utf-8

import http.client
import re
from xml.dom.minidom import parseString

from event import ModuleEvent
from xmlparser.node import ModuleState

nemubotversion = 3.3

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


def getPage (s, p):
    conn = http.client.HTTPConnection(s, timeout=10)
    try:
        conn.request("GET", p)
    except socket.gaierror:
        print ("[%s] impossible de récupérer la page %s."%(s, p))
        return None

    res = conn.getresponse()
    data = res.read()

    conn.close()
    return (res.status, data)

def station_status(station):
    """Gets available and free status of a given station"""
    (st, page) = getPage(CONF.getNode("server")["ip"], CONF.getNode("server")["url"] + station)
    if st == http.client.OK:
        response = parseString(page)
        available = response.documentElement.getElementsByTagName("available")
        if len(available) > 0:
            available = int(available[0].childNodes[0].nodeValue)
        else:
            available = 0
        free = response.documentElement.getElementsByTagName("free")
        if len(free) > 0:
            free = int(free[0].childNodes[0].nodeValue)
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
                        "%s: à la station %s : %d vélib et %d points d'attache"
                        " disponibles." % (msg.nick, station, available, free),
                        msg.channel)
    else:
        return Response(msg.sender,
                        "%s: station %s inconnue." % (msg.nick, station),
                        msg.channel)

def ask_stations(msg):
    """Hook entry from !velib"""
    global DATAS
    if len(msg.cmds) > 5:
        return Response(msg.sender,
                        "Demande-moi moins de stations à la fois.",
                        msg.channel, nick=msg.nick)
    elif len(msg.cmds) > 1:
        for station in msg.cmds[1:]:
            if re.match("^[0-9]{4,5}$", station):
                return print_station_status(msg, station)
            elif station in DATAS.index:
                return print_station_status(msg, DATAS.index[station]["number"])
            else:
                return Response(msg.sender,
                                "numéro de station invalide.",
                                msg.channel, nick=msg.nick)
    else:
        return Response(msg.sender,
                        "Pour quelle station ?",
                        msg.channel, nick=msg.nick)
