"""Inform about Free Mobile tarifs"""

# PYTHON STUFFS #######################################################

import urllib.parse
from bs4 import BeautifulSoup

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response


# MODULE CORE #########################################################

ACT = {
    "ff_toFixe": "Appel vers les fixes",
    "ff_toMobile": "Appel vers les mobiles",
    "ff_smsSendedToCountry": "SMS vers le pays",
    "ff_mmsSendedToCountry": "MMS vers le pays",
    "fc_callToFrance": "Appel vers la France",
    "fc_smsToFrance": "SMS vers la france",
    "fc_mmsSended": "MMS vers la france",
    "fc_callToSameCountry": "Réception des appels",
    "fc_callReceived": "Appel dans le pays",
    "fc_smsReceived": "SMS (Réception)",
    "fc_mmsReceived": "MMS (Réception)",
    "fc_moDataFromCountry": "Data",
}

def get_land_tarif(country, forfait="pkgFREE"):
    url = "http://mobile.international.free.fr/?" + urllib.parse.urlencode({'pays': country})
    page = web.getURLContent(url)
    soup = BeautifulSoup(page)

    fact = soup.find(class_=forfait)

    if fact is None:
        raise IMException("Country or forfait not found.")

    res = {}
    for s in ACT.keys():
        try:
            res[s] = fact.find(attrs={"data-bind": "text: " + s}).text + " " + fact.find(attrs={"data-bind": "html: " + s + "Unit"}).text
        except AttributeError:
            res[s] = "inclus"

    return res

@hook.command("freetarifs",
              help="Show Free Mobile tarifs for given contries",
              help_usage={"COUNTRY": "Show Free Mobile tarifs for given CONTRY"},
              keywords={
                  "forfait=FORFAIT": "Related forfait between Free (default) and 2euro"
              })
def get_freetarif(msg):
    res = Response(channel=msg.channel)

    for country in msg.args:
        t = get_land_tarif(country.lower().capitalize(), "pkg" + (msg.kwargs["forfait"] if "forfait" in msg.kwargs else "FREE").upper())
        res.append_message(["\x02%s\x0F : %s" % (ACT[k], t[k]) for k in sorted(ACT.keys(), reverse=True)], title=country)

    return res
