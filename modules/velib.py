# coding=utf-8

import http.client
import re
from xml.dom.minidom import parseString

from module_state import ModuleState

nemubotversion = 3.0

def load():
  global DATAS
  DATAS.setIndex("name", "station")


def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Gets information about velib stations"

def help_full ():
  return "!velib /number/ ...: gives available bikes and slots at the station /number/."


def getPage (s, p):
  conn = http.client.HTTPConnection(s)
  try:
    conn.request("GET", p)
  except socket.gaierror:
    print ("[%s] impossible de récupérer la page %s."%(s, p))
    return None

  res = conn.getresponse()
  data = res.read()

  conn.close()
  return (res.status, data)


def station_status(msg, station):
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
    msg.send_chn("%s: à la station %s : %d vélib et %d points d'attache disponibles." % (msg.nick, station, available, free))
  else:
    msg.send_chn("%s: station %s inconnue." % (msg.nick, station))

def parseanswer(msg):
  global DATAS
  if msg.cmd[0] == "velib":
    if len(msg.cmd) > 5:
      msg.send_chn("%s: Demande-moi moins de stations à la fois." % msg.nick)
    elif len(msg.cmd) > 1:
      for station in msg.cmd[1:]:
        if re.match("^[0-9]{4,5}$", station):
          station_status(msg, station)
        elif station in DATAS.index:
          station_status(msg, DATAS.index[station]["number"])
        else:
          msg.send_chn("%s: numéro de station invalide." % (msg.nick))
    else:
      msg.send_chn("%s: Pour quelle station ?" % msg.nick)
    return True
  else:
    return False
