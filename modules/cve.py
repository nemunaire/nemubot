from bs4 import BeautifulSoup
from urllib.parse import quote

from nemubot.hooks import hook
from nemubot.tools.web import getURLContent
from more import Response

"""CVE description"""

nemubotversion = 4.0

BASEURL_MITRE = 'http://cve.mitre.org/cgi-bin/cvename.cgi?name='


def get_cve(cve_id):
    search_url = BASEURL_MITRE + quote(cve_id.upper())

    soup = BeautifulSoup(getURLContent(search_url))
    desc = soup.body.findAll('td')

    return desc[17].text.replace("\n", " ") + " Moar at " + search_url

@hook.command("cve")
def get_cve_desc(msg):
    res = Response(channel=msg.channel)

    for cve_id in msg.args:
        if cve_id[:3].lower() != 'cve':
            cve_id = 'cve-' + cve_id

        res.append_message(get_cve(cve_id))

    return res
