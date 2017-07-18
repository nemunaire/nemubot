"""Retrieve flight information from VirtualRadar APIs"""

# PYTHON STUFFS #######################################################

import re
from urllib.parse import quote
import time

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response
import mapquest

# GLOBALS #############################################################

URL_API = "http://public-api.adsbexchange.com/VirtualRadar/AircraftList.json?fcallC=%s"

SPEED_TYPES = {
        0: 'Ground speed',
        1: 'Ground speed reversing',
        2: 'Indicated air speed',
        3: 'True air speed'}

WTC_CAT = {
        0: 'None',
        1: 'Light',
        2: 'Medium',
        3: 'Heavy'
        }

SPECIES = {
        1: 'Land plane',
        2: 'Sea plane',
        3: 'Amphibian',
        4: 'Helicopter',
        5: 'Gyrocopter',
        6: 'Tiltwing',
        7: 'Ground vehicle',
        8: 'Tower'}

HANDLER_TABLE = {
        'From': lambda x: 'From: \x02%s\x0F' % x,
        'To': lambda x: 'To: \x02%s\x0F' % x,
        'Op': lambda x: 'Airline: \x02%s\x0F' % x,
        'Mdl': lambda x: 'Model: \x02%s\x0F' % x,
        'Call': lambda x: 'Flight: \x02%s\x0F' % x,
        'PosTime': lambda x: 'Last update: \x02%s\x0F' % (time.ctime(int(x)/1000)),
        'Alt': lambda x: 'Altitude: \x02%s\x0F ft' % x,
        'Spd': lambda x: 'Speed: \x02%s\x0F kn' % x,
        'SpdTyp': lambda x: 'Speed type: \x02%s\x0F' % SPEED_TYPES[x] if x in SPEED_TYPES  else None,
        'Engines': lambda x: 'Engines: \x02%s\x0F' % x,
        'Gnd': lambda x: 'On the ground' if x else None,
        'Mil': lambda x: 'Military aicraft' if x else None,
        'Species': lambda x: 'Aircraft species: \x02%s\x0F' % SPECIES[x] if x in SPECIES  else None,
        'WTC': lambda x: 'Turbulence level: \x02%s\x0F' % WTC_CAT[x] if x in WTC_CAT  else None,
        }

# MODULE CORE #########################################################

def virtual_radar(flight_call):
    obj = web.getJSON(URL_API % quote(flight_call))

    if "acList" in obj:
        for flight in obj["acList"]:
            yield flight

def flight_info(flight):
    for prop in HANDLER_TABLE:
        if prop in flight:
            yield HANDLER_TABLE[prop](flight[prop])

# MODULE INTERFACE ####################################################

@hook.command("flight",
              help="Get flight information",
              help_usage={ "FLIGHT": "Get information on FLIGHT" })
def cmd_flight(msg):
    if not len(msg.args):
        raise IMException("please indicate a flight")

    res = Response(channel=msg.channel, nick=msg.frm,
                   nomore="No more flights", count=" (%s more flights)")

    for param in msg.args:
        for flight in virtual_radar(param):
            if 'Lat' in flight and 'Long' in flight:
                loc = None
                for location in  mapquest.geocode('{Lat},{Long}'.format(**flight)):
                    loc = location
                    break
                if loc:
                    res.append_message('\x02{0}\x0F: Position: \x02{1}\x0F, {2}'.format(flight['Call'], \
                            mapquest.where(loc), \
                            ', '.join(filter(None, flight_info(flight)))))
                    continue
            res.append_message('\x02{0}\x0F: {1}'.format(flight['Call'], \
                        ', '.join(filter(None, flight_info(flight)))))
    return res
