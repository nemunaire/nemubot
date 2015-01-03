# coding=utf-8

"""Informe les usagers des prochains passages des transports en communs de la RATP"""

from nemubot.hooks import hook
from more import Response

nemubotversion = 3.4

from .external.src import ratp

def help_full ():
    return "!ratp transport line [station]: Donne des informations sur les prochains passages du transport en commun séléctionné à l'arrêt désiré. Si aucune station n'est précisée, les liste toutes."


@hook("cmd_hook", "ratp")
def ask_ratp(msg):
    """Hook entry from !ratp"""
    if len(msg.cmds) == 4:
        transport = msg.cmds[1]
        line = msg.cmds[2]
        station = msg.cmds[3]
        times = ratp.getNextStopsAtStation(transport, line, station)

        if len(times) == 0:
            raise IRCException("la station %s n'existe pas sur le %s ligne %s." % (station, transport, line))

        (time, direction, stationname) = times[0]
        return Response(message=["\x03\x02%s\x03\x02 direction %s" % (time, direction) for time, direction, stationname in times],
                        title="Prochains passages du %s ligne %s à l'arrêt %s" % (transport, line, stationname),
                        channel=msg.channel)

    elif len(msg.cmds) == 3:
        stations = ratp.getAllStations(msg.cmds[1], msg.cmds[2])

        if len(stations) == 0:
            raise IRCException("aucune station trouvée.")
        return Response([s for s in stations], title="Stations", channel=msg.channel)

    else:
        raise IRCException("Mauvais usage, merci de spécifier un type de transport et une ligne, ou de consulter l'aide du module.")
