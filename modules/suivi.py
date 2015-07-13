import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

from nemubot.hooks import hook
from nemubot.exception import IRCException
from more import Response

nemubotversion = 3.4

def help_full():
    return "Traquez vos courriers La Poste en utilisant la commande: !laposte <tracking number>\nCe service se base sur http://www.csuivi.courrier.laposte.fr/suivi/index"

def get_colissimo_info(colissimo_id):
    data = urllib.parse.urlencode({'colispart': colissimo_id})
    colissimo_baseurl = "http://www.colissimo.fr/portail_colissimo/suivre.do"
    colissimo_data = urllib.request.urlopen(colissimo_baseurl, data.encode('utf-8'))
    soup = BeautifulSoup(colissimo_data)

    dataArray = soup.find(class_='dataArray')
    if dataArray and dataArray.tbody and dataArray.tbody.tr:
        date = dataArray.tbody.tr.find(headers="Date").get_text()
        libelle = dataArray.tbody.tr.find(headers="Libelle").get_text()
        site = dataArray.tbody.tr.find(headers="site").get_text().strip()
        return (date, libelle, site.strip())

def get_laposte_info(laposte_id):
    data = urllib.parse.urlencode({'id': laposte_id})
    laposte_baseurl = "http://www.part.csuivi.courrier.laposte.fr/suivi/index"

    laposte_data = urllib.request.urlopen(laposte_baseurl, data.encode('utf-8'))
    soup = BeautifulSoup(laposte_data)
    search_res = soup.find(class_='resultat_rech_simple_table').tbody.tr
    if (soup.find(class_='resultat_rech_simple_table').thead
            and soup.find(class_='resultat_rech_simple_table').thead.tr):
        field = search_res.find('td')
        poste_id = field.get_text()

        field = field.find_next('td')
        poste_type = field.get_text()

        field = field.find_next('td')
        poste_date = field.get_text()

        field = field.find_next('td')
        poste_location = field.get_text()

        field = field.find_next('td')
        poste_status = field.get_text()
        return (poste_type.lower(), poste_id.strip(), poste_status.lower(), poste_location, poste_date)


@hook("cmd_hook", "colissimo")
def get_colissimo_tracking_info(msg):
    if not len(msg.args):
        raise IRCException("Renseignez un identifiant d'envoi,")
    info = get_colissimo_info(msg.args[0])
    if info:
        date, libelle, site = info
        return Response("Colis: \x02%s\x0F : \x02%s\x0F Dernière mise à jour le \x02%s\x0F au site \x02%s\x0F." % (msg.args[0], libelle, date, site), msg.channel)
    return Response("L'identifiant recherché semble incorrect, merci de vérifier son exactitude.", msg.channel)

@hook("cmd_hook", "laposte")
def get_laposte_tracking_info(msg):
    if not len(msg.args):
        raise IRCException("Renseignez un identifiant d'envoi,")
    info = get_laposte_info(msg.args[0])
    if info:
        poste_type, poste_id, poste_status, poste_location, poste_date = info
        return Response("Le courrier de type \x02%s\x0F : \x02%s\x0F est actuellement \x02%s\x0F dans la zone \x02%s\x0F (Mis à jour le \x02%s\x0F)." % (poste_type, poste_id, poste_status, poste_location, poste_date), msg.channel)
    return Response("L'identifiant recherché semble incorrect, merci de vérifier son exactitude.", msg.channel)
