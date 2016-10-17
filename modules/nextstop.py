"""Informe les usagers des prochains passages des transports en communs de la RATP"""

# PYTHON STUFFS #######################################################

from nemubot.exception import IMException
from nemubot.hooks import hook
from more import Response

from nextstop import ratp

@hook.command("ratp",
              help="Affiche les prochains horaires de passage",
              help_usage={
                  "TRANSPORT": "Affiche les lignes du moyen de transport donné",
                  "TRANSPORT LINE": "Affiche les stations sur la ligne de transport donnée",
                  "TRANSPORT LINE STATION": "Affiche les prochains horaires de passage à l'arrêt donné",
                  "TRANSPORT LINE STATION DESTINATION": "Affiche les prochains horaires de passage dans la direction donnée",
              })
def ask_ratp(msg):
    l = len(msg.args)

    transport = msg.args[0] if l > 0 else None
    line = msg.args[1] if l > 1 else None
    station = msg.args[2] if l > 2 else None
    direction = msg.args[3] if l > 3 else None

    if station is not None:
        times = sorted(ratp.getNextStopsAtStation(transport, line, station, direction), key=lambda i: i[0])

        if len(times) == 0:
            raise IMException("la station %s n'existe pas sur le %s ligne %s." % (station, transport, line))

        (time, direction, stationname) = times[0]
        return Response(message=["\x03\x02%s\x03\x02 direction %s" % (time, direction) for time, direction, stationname in times],
                        title="Prochains passages du %s ligne %s à l'arrêt %s" % (transport, line, stationname),
                        channel=msg.channel)

    elif line is not None:
        stations = ratp.getAllStations(transport, line)

        if len(stations) == 0:
            raise IMException("aucune station trouvée.")
        return Response(stations, title="Stations", channel=msg.channel)

    elif transport is not None:
        lines = ratp.getTransportLines(transport)
        if len(lines) == 0:
            raise IMException("aucune ligne trouvée.")
        return Response(lines, title="Lignes", channel=msg.channel)

    else:
        raise IMException("précise au moins un moyen de transport.")


@hook.command("ratp_alert",
              help="Affiche les perturbations en cours sur le réseau")
def ratp_alert(msg):
    if len(msg.args) == 0:
        raise IMException("précise au moins un moyen de transport.")

    l = len(msg.args)
    transport = msg.args[0] if l > 0 else None
    line = msg.args[1] if l > 1 else None

    if line is not None:
        d = ratp.getDisturbanceFromLine(transport, line)
        if "date" in d and d["date"] is not None:
            incidents = "Au {date[date]}, {title}: {message}".format(**d)
        else:
            incidents = "{title}: {message}".format(**d)
    else:
        incidents = ratp.getDisturbance(None, transport)

    return Response(incidents, channel=msg.channel, nomore="No more incidents", count=" (%d more incidents)")
