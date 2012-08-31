# coding=utf-8

import http.client
import re
from xml.dom.minidom import parseString

from event import ModuleEvent
from xmlparser.node import ModuleState
from .external.src import ratp


nemubotversion = 3.2

def load(context):
  global DATAS
  DATAS.setIndex("name", "station")


def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Informe les usagers des prochains passages des transports en communs de la RATP"

def help_full ():
  return "!ratp transport line [station]: Donne des informations sur les prochains passages du transport en commun séléctionné à l'arrêt désiré. Si aucune station n'est précisée, les liste toutes."


def extractInformation(msg,
    transport,
    line,
    station):
  if station is not None and station != "":
    times = ratp.getNextStopsAtStation(transport, line, station)
    stops = ""
    for time, direction, stationname in times:
      station = stationname
      stops += time+" direction "+direction+"; "
    if len(stops) > 0:
      msg.send_chn("%s: Prochains passages du %s ligne %s à l'arrêt %s: %s" %
          (msg.nick, transport, line, stationname, stops))
    else:
      msg.send_chn("%s: La station `%s' ne semble pas exister sur le %s ligne %s."
          % (msg.nick, station, transport, line))
  else:
    stations = ratp.getAllStations(transport, line)
    if len(stations) > 0:
      s = ""
      for name in stations:
        s += name + "; "
      msg.send_chn("%s: Stations: %s." % (msg.nick, s))
      return 0
    else:
      msg.send_chn("%s: Aucune station trouvée." % msg.nick)

def ask_ratp(msg):
    """Hook entry from !ratp"""
    global DATAS
    if len(msg.cmd) == 4:
        extractInformation(msg, msg.cmd[1], msg.cmd[2], msg.cmd[3])
        return True
    elif len(msg.cmd) == 3:
        extractInformation(msg, msg.cmd[1], msg.cmd[2], None)
    else:
        msg.send_chn("%s: Mauvais usage, merci de spécifier un type de transport et une ligne, ou de consulter l'aide du module." % msg.nick)
    return False

