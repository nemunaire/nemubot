import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

from nemubot.hooks import hook
from nemubot.exception import IRCException
from more import Response

nemubotversion = 3.4

def help_full():
    return "Traquez vos courriers La Poste en utilisant la commande: !laposte <tracking number>\nCe service se base sur http://www.csuivi.courrier.laposte.fr/suivi/index"


@hook("cmd_hook", "laposte")
def get_tracking_info(msg):
    if not len(msg.args):
        raise IRCException("Renseignez un identifiant d'envoi,")

    data = urllib.parse.urlencode({'id': msg.args[0]})
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

       return Response("Le courrier de type \x02%s\x0F : \x02%s\x0F est actuellement \x02%s\x0F dans la zone \x02%s\x0F (Mis à jour le \x02%s\x0F)." % (poste_type.lower(), poste_id.strip(), poste_status.lower(), poste_location, poste_date), msg.channel)
    return Response("L'identifiant recherché semble incorrect, merci de vérifier son exactitude.", msg.channel)
