"""Read CVE in your IM client"""

# PYTHON STUFFS #######################################################

from bs4 import BeautifulSoup
from urllib.parse import quote

from nemubot.hooks import hook
from nemubot.tools.web import getURLContent, striphtml

from more import Response

BASEURL_NIST = 'https://web.nvd.nist.gov/view/vuln/detail?vulnId='


# MODULE CORE #########################################################

def get_cve(cve_id):
    search_url = BASEURL_NIST + quote(cve_id.upper())

    soup = BeautifulSoup(getURLContent(search_url))
    vuln = soup.body.find(class_="vulnDetail")
    cvss = vuln.find(class_="cvssDetail")

    return [
        "Base score: " + cvss.findAll('div')[0].findAll('a')[0].text.strip(),
        vuln.findAll('p')[0].text, # description
        striphtml(vuln.findAll('div')[0].text).strip(), # publication date
        striphtml(vuln.findAll('div')[1].text).strip(), # last revised
    ]


# MODULE INTERFACE ####################################################

@hook.command("cve",
              help="Display given CVE",
              help_usage={"CVE_ID": "Display the description of the given CVE"})
def get_cve_desc(msg):
    res = Response(channel=msg.channel)

    for cve_id in msg.args:
        if cve_id[:3].lower() != 'cve':
            cve_id = 'cve-' + cve_id

        res.append_message(get_cve(cve_id))

    return res
