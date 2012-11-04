# coding=utf-8

import http.client
import re
from xml.dom.minidom import parseString

from .external.src import ratp

nemubotversion = 3.3

def load(context):
  global DATAS
  DATAS.setIndex("name", "station")


def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "Informe les usagers des prochains passages des transports en communs de la RATP"

def help_full ():
    return "!ratp transport line [station]: Donne des informations sur les prochains passages du transport en commun séléctionné à l'arrêt désiré. Si aucune station n'est précisée, les liste toutes."


def extractInformation(msg, transport, line, station=None):
  if station is not None and station != "":
    times = ratp.getNextStopsAtStation(transport, line, station)
    if len(times) > 0:
      (time, direction, stationname) = times[0]
      return Response(msg.sender, message=["\x03\x02"+time+"\x03\x02 direction "+direction for time, direction, stationname in times], title="Prochains passages du %s ligne %s à l'arrêt %s" %
          (transport, line, stationname), channel=msg.channel)
    else:
      return Response(msg.sender, "La station `%s' ne semble pas exister sur le %s ligne %s."
          % (station, transport, line), msg.channel)
  else:
    stations = ratp.getAllStations(transport, line)
    if len(stations) > 0:
      return Response(msg.sender, [s for s in stations], title="Stations", channel=msg.channel)
    else:
      return Response(msg.sender, "Aucune station trouvée.", msg.channel)

def ask_ratp(msg):
    """Hook entry from !ratp"""
    global DATAS
    if len(msg.cmds) == 4:
        return extractInformation(msg, msg.cmds[1], msg.cmds[2], msg.cmds[3])
    elif len(msg.cmds) == 3:
        return extractInformation(msg, msg.cmds[1], msg.cmds[2])
    else:
        return Response(msg.sender, "Mauvais usage, merci de spécifier un type de transport et une ligne, ou de consulter l'aide du module.", msg.channel, msg.nick)
    return False
