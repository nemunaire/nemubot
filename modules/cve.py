"""Read CVE in your IM client"""

# PYTHON STUFFS #######################################################

from bs4 import BeautifulSoup
from urllib.parse import quote

from nemubot.hooks import hook
from nemubot.tools.web import getURLContent, striphtml

from more import Response

BASEURL_NIST = 'https://nvd.nist.gov/vuln/detail/'


# MODULE CORE #########################################################

def get_cve(cve_id):
    search_url = BASEURL_NIST + quote(cve_id.upper())

    soup = BeautifulSoup(getURLContent(search_url))

    return {
        "description": soup.body.find(attrs={"data-testid":"vuln-description"}).text.strip(),
        "published": soup.body.find(attrs={"data-testid":"vuln-published-on"}).text.strip(),
        "last_modified": soup.body.find(attrs={"data-testid":"vuln-last-modified-on"}).text.strip(),
        "source": soup.body.find(attrs={"data-testid":"vuln-source"}).text.strip(),

        "base_score": float(soup.body.find(attrs={"data-testid":"vuln-cvssv3-base-score-link"}).text.strip()),
        "severity": soup.body.find(attrs={"data-testid":"vuln-cvssv3-base-score-severity"}).text.strip(),
        "impact_score": float(soup.body.find(attrs={"data-testid":"vuln-cvssv3-impact-score"}).text.strip()),
        "exploitability_score": float(soup.body.find(attrs={"data-testid":"vuln-cvssv3-exploitability-score"}).text.strip()),

        "av": soup.body.find(attrs={"data-testid":"vuln-cvssv3-av"}).text.strip(),
        "ac": soup.body.find(attrs={"data-testid":"vuln-cvssv3-ac"}).text.strip(),
        "pr": soup.body.find(attrs={"data-testid":"vuln-cvssv3-pr"}).text.strip(),
        "ui": soup.body.find(attrs={"data-testid":"vuln-cvssv3-ui"}).text.strip(),
        "s": soup.body.find(attrs={"data-testid":"vuln-cvssv3-s"}).text.strip(),
        "c": soup.body.find(attrs={"data-testid":"vuln-cvssv3-c"}).text.strip(),
        "i": soup.body.find(attrs={"data-testid":"vuln-cvssv3-i"}).text.strip(),
        "a": soup.body.find(attrs={"data-testid":"vuln-cvssv3-a"}).text.strip(),
    }


def display_metrics(av, ac, pr, ui, s, c, i, a, **kwargs):
    ret = []
    if av != "None": ret.append("Attack Vector: \x02%s\x0F" % av)
    if ac != "None": ret.append("Attack Complexity: \x02%s\x0F" % ac)
    if pr != "None": ret.append("Privileges Required: \x02%s\x0F" % pr)
    if ui != "None": ret.append("User Interaction: \x02%s\x0F" % ui)
    if s != "Unchanged": ret.append("Scope: \x02%s\x0F" % s)
    if c != "None": ret.append("Confidentiality: \x02%s\x0F" % c)
    if i != "None": ret.append("Integrity: \x02%s\x0F" % i)
    if a != "None": ret.append("Availability: \x02%s\x0F" % a)
    return ', '.join(ret)


# MODULE INTERFACE ####################################################

@hook.command("cve",
              help="Display given CVE",
              help_usage={"CVE_ID": "Display the description of the given CVE"})
def get_cve_desc(msg):
    res = Response(channel=msg.channel)

    for cve_id in msg.args:
        if cve_id[:3].lower() != 'cve':
            cve_id = 'cve-' + cve_id

        cve = get_cve(cve_id)
        metrics = display_metrics(**cve)
        res.append_message("{cveid}: Base score: \x02{base_score} {severity}\x0F (impact: \x02{impact_score}\x0F, exploitability: \x02{exploitability_score}\x0F; {metrics}), from \x02{source}\x0F, last modified on \x02{last_modified}\x0F. {description}".format(cveid=cve_id, metrics=metrics, **cve))

    return res
