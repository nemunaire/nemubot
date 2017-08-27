"""Read CVE in your IM client"""

# PYTHON STUFFS #######################################################

from bs4 import BeautifulSoup
from urllib.parse import quote

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools.web import getURLContent, striphtml

from nemubot.module.more import Response

BASEURL_NIST = 'https://nvd.nist.gov/vuln/detail/'


# MODULE CORE #########################################################

VULN_DATAS = {
    "alert-title": "vuln-warning-status-name",
    "alert-content": "vuln-warning-banner-content",

    "description": "vuln-description",
    "published": "vuln-published-on",
    "last_modified": "vuln-last-modified-on",
    "source": "vuln-source",

    "base_score": "vuln-cvssv3-base-score-link",
    "severity": "vuln-cvssv3-base-score-severity",
    "impact_score": "vuln-cvssv3-impact-score",
    "exploitability_score": "vuln-cvssv3-exploitability-score",

    "av": "vuln-cvssv3-av",
    "ac": "vuln-cvssv3-ac",
    "pr": "vuln-cvssv3-pr",
    "ui": "vuln-cvssv3-ui",
    "s": "vuln-cvssv3-s",
    "c": "vuln-cvssv3-c",
    "i": "vuln-cvssv3-i",
    "a": "vuln-cvssv3-a",
}


def get_cve(cve_id):
    search_url = BASEURL_NIST + quote(cve_id.upper())

    soup = BeautifulSoup(getURLContent(search_url))

    vuln = {}

    for vd in VULN_DATAS:
        r = soup.body.find(attrs={"data-testid": VULN_DATAS[vd]})
        if r:
            vuln[vd] = r.text.strip()

    return vuln


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
        if not cve:
            raise IMException("CVE %s doesn't exists." % cve_id)

        if "alert-title" in cve or "alert-content" in cve:
            alert = "\x02%s:\x0F %s " % (cve["alert-title"] if "alert-title" in cve else "",
                                         cve["alert-content"] if "alert-content" in cve else "")
        else:
            alert = ""

        if "base_score" not in cve and "description" in cve:
            res.append_message("{alert}From \x02{source}\x0F, last modified on \x02{last_modified}\x0F. {description}".format(alert=alert, **cve), title=cve_id)
        else:
            metrics = display_metrics(**cve)
            res.append_message("{alert}Base score: \x02{base_score} {severity}\x0F (impact: \x02{impact_score}\x0F, exploitability: \x02{exploitability_score}\x0F; {metrics}), from \x02{source}\x0F, last modified on \x02{last_modified}\x0F. {description}".format(alert=alert, metrics=metrics, **cve), title=cve_id)

    return res
