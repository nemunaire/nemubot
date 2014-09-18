# coding=utf-8

"""Informe les usagers des prochains passages des transports en communs de la RATP"""

import http.client
import re
from xml.dom.minidom import parseString

from .external.src import ratp

nemubotversion = 3.4

def load(context):
  global DATAS
  DATAS.setIndex("name", "station")


def help_full ():
    return "!ratp transport line [station]: Donne des informations sur les prochains passages du transport en commun séléctionné à l'arrêt désiré. Si aucune station n'est précisée, les liste toutes."


def extractInformation(msg, transport, line, station=None):
  if station is not None and station != "":
    times = ratp.getNextStopsAtStation(transport, line, station)
    if len(times) > 0:
      (time, direction, stationname) = times[0]
      return Response(message=["\x03\x02"+time+"\x03\x02 direction "+direction for time, direction, stationname in times], title="Prochains passages du %s ligne %s à l'arrêt %s" %
          (transport, line, stationname), channel=msg.channel)
    else:
      raise IRCException("La station `%s' ne semble pas exister sur le %s ligne %s."
          % (station, transport, line))
  else:
    stations = ratp.getAllStations(transport, line)
    if len(stations) == 0:
        raise IRCException("aucune station trouvée.")
    return Response([s for s in stations], title="Stations", channel=msg.channel)

def ask_ratp(msg):
    """Hook entry from !ratp"""
    global DATAS
    if len(msg.cmds) == 4:
        return extractInformation(msg, msg.cmds[1], msg.cmds[2], msg.cmds[3])
    elif len(msg.cmds) == 3:
        return extractInformation(msg, msg.cmds[1], msg.cmds[2])
    else:
        raise IRCException("Mauvais usage, merci de spécifier un type de transport et une ligne, ou de consulter l'aide du module.")
    return False
