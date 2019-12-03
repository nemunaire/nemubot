"""Postal tracking module"""

# PYTHON STUFF ############################################

import json
import urllib.parse
from bs4 import BeautifulSoup
import re

from nemubot.hooks import hook
from nemubot.exception import IMException
from nemubot.tools.web import getURLContent, getURLHeaders, getJSON
from nemubot.module.more import Response


# POSTAGE SERVICE PARSERS ############################################

def get_tnt_info(track_id):
    values = []
    data = getURLContent('https://www.tnt.fr/public/suivi_colis/recherche/visubontransport.do?bonTransport=%s' % track_id)
    soup = BeautifulSoup(data)
    status_list = soup.find('div', class_='result__content')
    if not status_list:
        return None
    last_status = status_list.find('div', class_='roster')
    if last_status:
        for info in last_status.find_all('div', class_='roster__item'):
            values.append(info.get_text().strip())
    if len(values) == 3:
        return (values[0], values[1], values[2])


def get_colissimo_info(colissimo_id):
    colissimo_data = getURLContent("https://www.laposte.fr/particulier/outils/suivre-vos-envois?code=%s" % colissimo_id)
    soup = BeautifulSoup(colissimo_data)

    dataArray = soup.find(class_='results-suivi')
    if dataArray and dataArray.table and dataArray.table.tbody and dataArray.table.tbody.tr:
        td = dataArray.table.tbody.tr.find_all('td')
        if len(td) > 2:
            date = td[0].get_text()
            libelle = re.sub(r'[\n\t\r]', '', td[1].get_text())
            site = td[2].get_text().strip()
            return (date, libelle, site.strip())


def get_chronopost_info(track_id):
    data = urllib.parse.urlencode({'listeNumeros': track_id})
    track_baseurl = "https://www.chronopost.fr/expedier/inputLTNumbersNoJahia.do?lang=fr_FR"
    track_data = getURLContent(track_baseurl, data.encode('utf-8'))
    soup = BeautifulSoup(track_data)

    infoClass = soup.find(class_='numeroColi2')
    if infoClass and infoClass.get_text():
        info = infoClass.get_text().split("\n")
        if len(info) >= 1:
            info = info[1].strip().split("\"")
            if len(info) >= 2:
                date = info[2]
                libelle = info[1]
                return (date, libelle)


def get_colisprive_info(track_id):
    data = urllib.parse.urlencode({'numColis': track_id})
    track_baseurl = "https://www.colisprive.com/moncolis/pages/detailColis.aspx"
    track_data = getURLContent(track_baseurl, data.encode('utf-8'))
    soup = BeautifulSoup(track_data)

    dataArray = soup.find(class_='BandeauInfoColis')
    if (dataArray and dataArray.find(class_='divStatut')
            and dataArray.find(class_='divStatut').find(class_='tdText')):
        status = dataArray.find(class_='divStatut') \
                          .find(class_='tdText').get_text()
        return status


def get_ups_info(track_id):
    data = json.dumps({'Locale': "en_US", 'TrackingNumber': [track_id]})
    track_baseurl = "https://www.ups.com/track/api/Track/GetStatus?loc=en_US"
    track_data = getJSON(track_baseurl, data.encode('utf-8'), header={"Content-Type": "application/json"})
    return (track_data["trackDetails"][0]["trackingNumber"],
            track_data["trackDetails"][0]["packageStatus"],
            track_data["trackDetails"][0]["shipmentProgressActivities"][0]["date"] + " " + track_data["trackDetails"][0]["shipmentProgressActivities"][0]["time"],
            track_data["trackDetails"][0]["shipmentProgressActivities"][0]["location"],
            track_data["trackDetails"][0]["shipmentProgressActivities"][0]["activityScan"])


def get_laposte_info(laposte_id):
    status, laposte_headers = getURLHeaders("https://www.laposte.fr/outils/suivre-vos-envois?" + urllib.parse.urlencode({'code': laposte_id}))

    laposte_cookie = None
    for k,v in laposte_headers:
        if k.lower() == "set-cookie" and v.find("access_token") >= 0:
            laposte_cookie = v.split(";")[0]

    laposte_data = getJSON("https://api.laposte.fr/ssu/v1/suivi-unifie/idship/%s?lang=fr_FR" % urllib.parse.quote(laposte_id), header={"Accept": "application/json", "Cookie": laposte_cookie})

    shipment = laposte_data["shipment"]
    return (shipment["product"], shipment["idShip"], shipment["event"][0]["label"], shipment["event"][0]["date"])


def get_postnl_info(postnl_id):
    data = urllib.parse.urlencode({'barcodes': postnl_id})
    postnl_baseurl = "http://www.postnl.post/details/"

    postnl_data = getURLContent(postnl_baseurl, data.encode('utf-8'))
    soup = BeautifulSoup(postnl_data)
    if (soup.find(id='datatables')
            and soup.find(id='datatables').tbody
            and soup.find(id='datatables').tbody.tr):
        search_res = soup.find(id='datatables').tbody.tr
        if len(search_res.find_all('td')) >= 3:
            field = field.find_next('td')
            post_date = field.get_text()

            field = field.find_next('td')
            post_status = field.get_text()

            field = field.find_next('td')
            post_destination = field.get_text()

            return (post_status.lower(), post_destination, post_date)


def get_usps_info(usps_id):
    usps_parcelurl = "https://tools.usps.com/go/TrackConfirmAction_input?" + urllib.parse.urlencode({'qtc_tLabels1': usps_id})

    usps_data = getURLContent(usps_parcelurl)
    soup = BeautifulSoup(usps_data)
    if (soup.find(id="trackingHistory_1")
            and soup.find(class_="tracking_history").find(class_="row_notification")
            and soup.find(class_="tracking_history").find(class_="row_top").find_all("td")):
        notification = soup.find(class_="tracking_history").find(class_="row_notification").text.strip()
        date = re.sub(r"\s+", " ", soup.find(class_="tracking_history").find(class_="row_top").find_all("td")[0].text.strip())
        status = soup.find(class_="tracking_history").find(class_="row_top").find_all("td")[1].text.strip()
        last_location = soup.find(class_="tracking_history").find(class_="row_top").find_all("td")[2].text.strip()

        print(notification)

        return (notification, date, status, last_location)


def get_fedex_info(fedex_id, lang="en_US"):
    data = urllib.parse.urlencode({
        'data': json.dumps({
            "TrackPackagesRequest": {
                "appType": "WTRK",
                "appDeviceType": "DESKTOP",
                "uniqueKey": "",
                "processingParameters": {},
                "trackingInfoList": [
                    {
                        "trackNumberInfo": {
                            "trackingNumber": str(fedex_id),
                            "trackingQualifier": "",
                            "trackingCarrier": ""
                        }
                    }
                ]
            }
        }),
        'action': "trackpackages",
        'locale': lang,
        'version': 1,
        'format': "json"
    })
    fedex_baseurl = "https://www.fedex.com/trackingCal/track"

    fedex_data = getJSON(fedex_baseurl, data.encode('utf-8'))

    if ("TrackPackagesResponse" in fedex_data and
        "packageList" in fedex_data["TrackPackagesResponse"] and
        len(fedex_data["TrackPackagesResponse"]["packageList"]) and
        (not fedex_data["TrackPackagesResponse"]["errorList"][0]["code"] or
        fedex_data["TrackPackagesResponse"]["errorList"][0]["code"] == '0') and
        not fedex_data["TrackPackagesResponse"]["packageList"][0]["errorList"][0]["code"]
    ):
        return fedex_data["TrackPackagesResponse"]["packageList"][0]


def get_dhl_info(dhl_id, lang="en"):
    dhl_parcelurl = "http://www.dhl.com/shipmentTracking?" + urllib.parse.urlencode({'AWB': dhl_id})

    dhl_data = getJSON(dhl_parcelurl)

    if "results" in dhl_data and dhl_data["results"]:
        return dhl_data["results"][0]


# TRACKING HANDLERS ###################################################

def handle_tnt(tracknum):
    info = get_tnt_info(tracknum)
    if info:
        status, date, place = info
        placestr = ''
        if place:
            placestr = ' à \x02{place}\x0f'
        return ('Le colis \x02{trackid}\x0f a actuellement le status: '
                '\x02{status}\x0F mis à jour le \x02{date}\x0f{place}.'
                .format(trackid=tracknum, status=status,
                        date=re.sub(r'\s+', ' ', date), place=placestr))


def handle_laposte(tracknum):
    info = get_laposte_info(tracknum)
    if info:
        poste_type, poste_id, poste_status, poste_date = info
        return ("\x02%s\x0F : \x02%s\x0F est actuellement "
                "\x02%s\x0F (Mis à jour le \x02%s\x0F"
                ")." % (poste_type, poste_id, poste_status, poste_date))


def handle_postnl(tracknum):
    info = get_postnl_info(tracknum)
    if info:
        post_status, post_destination, post_date = info
        return ("PostNL \x02%s\x0F est actuellement "
                "\x02%s\x0F vers le pays \x02%s\x0F (Mis à jour le \x02%s\x0F"
                ")." % (tracknum, post_status, post_destination, post_date))


def handle_usps(tracknum):
    info = get_usps_info(tracknum)
    if info:
        notif, last_date, last_status, last_location = info
        return ("USPS \x02{tracknum}\x0F: {last_status} in \x02{last_location}\x0F as of {last_date}: {notif}".format(tracknum=tracknum, notif=notif, last_date=last_date, last_status=last_status.lower(), last_location=last_location))


def handle_ups(tracknum):
    info = get_ups_info(tracknum)
    if info:
        tracknum, status, last_date, last_location, last_status  = info
        return ("UPS \x02{tracknum}\x0F: {status}: in \x02{last_location}\x0F as of {last_date}: {last_status}".format(tracknum=tracknum, status=status, last_date=last_date, last_status=last_status.lower(), last_location=last_location))


def handle_colissimo(tracknum):
    info = get_colissimo_info(tracknum)
    if info:
        date, libelle, site = info
        return ("Colissimo: \x02%s\x0F : \x02%s\x0F Dernière mise à jour le "
                "\x02%s\x0F au site \x02%s\x0F."
                % (tracknum, libelle, date, site))


def handle_chronopost(tracknum):
    info = get_chronopost_info(tracknum)
    if info:
        date, libelle = info
        return ("Colis Chronopost: \x02%s\x0F : \x02%s\x0F. Dernière mise à "
                "jour \x02%s\x0F." % (tracknum, libelle, date))


def handle_coliprive(tracknum):
    info = get_colisprive_info(tracknum)
    if info:
        return ("Colis Privé: \x02%s\x0F : \x02%s\x0F." % (tracknum, info))


def handle_fedex(tracknum):
    info = get_fedex_info(tracknum)
    if info:
        if info["displayActDeliveryDateTime"] != "":
            return ("{trackingCarrierDesc}: \x02{statusWithDetails}\x0F: in \x02{statusLocationCity}, {statusLocationCntryCD}\x0F, delivered on: {displayActDeliveryDateTime}.".format(**info))
        elif info["statusLocationCity"] != "":
            return ("{trackingCarrierDesc}: \x02{statusWithDetails}\x0F: estimated delivery: {displayEstDeliveryDateTime}.".format(**info))
        else:
            return ("{trackingCarrierDesc}: \x02{statusWithDetails}\x0F: in \x02{statusLocationCity}, {statusLocationCntryCD}\x0F, estimated delivery: {displayEstDeliveryDateTime}.".format(**info))


def handle_dhl(tracknum):
    info = get_dhl_info(tracknum)
    if info:
        return "DHL {label} {id}: \x02{description}\x0F".format(**info)


TRACKING_HANDLERS = {
    'laposte': handle_laposte,
    'postnl': handle_postnl,
    'colissimo': handle_colissimo,
    'chronopost': handle_chronopost,
    'coliprive': handle_coliprive,
    'tnt': handle_tnt,
    'fedex': handle_fedex,
    'dhl': handle_dhl,
    'usps': handle_usps,
    'ups': handle_ups,
}


# HOOKS ##############################################################

@hook.command("track",
      help="Track postage delivery",
      help_usage={
          "TRACKING_ID [...]": "Track the specified postage IDs on various tracking services."
      },
      keywords={
          "tracker=TRK": "Precise the tracker (default: all) among: " + ', '.join(TRACKING_HANDLERS)
      })
def get_tracking_info(msg):
    if not len(msg.args):
        raise IMException("Renseignez un identifiant d'envoi.")

    res = Response(channel=msg.channel, count=" (%d suivis supplémentaires)")

    if 'tracker' in msg.kwargs:
        if msg.kwargs['tracker'] in TRACKING_HANDLERS:
            trackers = {
                msg.kwargs['tracker']: TRACKING_HANDLERS[msg.kwargs['tracker']]
            }
        else:
            raise IMException("No tracker named \x02{tracker}\x0F, please use"
                               " one of the following: \x02{trackers}\x0F"
                               .format(tracker=msg.kwargs['tracker'],
                                       trackers=', '
                                       .join(TRACKING_HANDLERS.keys())))
    else:
        trackers = TRACKING_HANDLERS

    for tracknum in msg.args:
        for name, tracker in trackers.items():
            ret = tracker(tracknum)
            if ret:
                res.append_message(ret)
                break
        if not ret:
            res.append_message("L'identifiant \x02{id}\x0F semble incorrect,"
                               " merci de vérifier son exactitude."
                               .format(id=tracknum))
    return res
