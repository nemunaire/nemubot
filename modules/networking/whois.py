import datetime
import urllib

from nemubot.exception import IRCException
from nemubot.tools.web import getJSON

from more import Response

URL_WHOIS = "http://www.whoisxmlapi.com/whoisserver/WhoisService?rid=1&domainName=%%s&outputFormat=json&userName=%s&password=%s"

def load(CONF, add_hook):
    global URL_WHOIS

    if not CONF or not CONF.hasNode("whoisxmlapi") or not CONF.getNode("whoisxmlapi").hasAttribute("username") or not CONF.getNode("whoisxmlapi").hasAttribute("password"):
        raise ImportError("You need a WhoisXML API account in order to use "
                          "the !netwhois feature. Add it to the module "
                          "configuration file:\n<whoisxmlapi username=\"XX\" "
                          "password=\"XXX\" />\nRegister at "
                          "http://www.whoisxmlapi.com/newaccount.php")

    URL_WHOIS = URL_WHOIS % (urllib.parse.quote(CONF.getNode("whoisxmlapi")["username"]), urllib.parse.quote(CONF.getNode("whoisxmlapi")["password"]))

    import nemubot.hooks
    add_hook("cmd_hook", nemubot.hooks.Message(cmd_whois, "netwhois",
                                               help="Get whois information about given domains",
                                               help_usage={"DOMAIN": "Return whois information on the given DOMAIN"}))


def extractdate(str):
    tries = [
        "%Y-%m-%dT%H:%M:%S.0%Z",
        "%Y-%m-%dT%H:%M:%S%Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.0Z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.0%Z",
        "%Y-%m-%d %H:%M:%S%Z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S.0Z",
        "%Y-%m-%d %H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]

    for t in tries:
        try:
            return datetime.datetime.strptime(str, t)
        except ValueError:
            pass
    return datetime.datetime.strptime(str, t)


def whois_entityformat(entity):
    ret = ""
    if "organization" in entity:
        ret += entity["organization"]
    if "name" in entity:
        ret += entity["name"]

    if "country" in entity or "city" in entity or "telephone" in entity or "email" in entity:
        ret += " (from "
        if "street1" in entity:
            ret += entity["street1"] + " "
        if "city" in entity:
            ret += entity["city"] + " "
        if "state" in entity:
            ret += entity["state"] + " "
        if "country" in entity:
            ret += entity["country"] + " "
        if "telephone" in entity:
            ret += entity["telephone"] + " "
        if "email" in entity:
            ret += entity["email"] + " "
        ret = ret.rstrip() + ")"

    return ret.lstrip()


def cmd_whois(msg):
    if not len(msg.args):
        raise IRCException("Indiquer un domaine ou une IP à whois !")

    dom = msg.args[0]

    js = getJSON(URL_WHOIS % urllib.parse.quote(dom))

    if "ErrorMessage" in js:
        err = js["ErrorMessage"]
        raise IRCException(js["ErrorMessage"]["msg"])

    whois = js["WhoisRecord"]

    res = Response(channel=msg.channel, nomore="No more whois information")

    res.append_message("%s: %s%s%s%s\x03\x02registered by\x03\x02 %s, \x03\x02administrated by\x03\x02 %s, \x03\x02managed by\x03\x02 %s" % (whois["domainName"],
                                                             whois["status"].replace("\n", ", ") + " " if "status" in whois else "",
                                                             "\x03\x02created on\x03\x02 " + extractdate(whois["createdDate"]).strftime("%c") + ", " if "createdDate" in whois else "",
                                                             "\x03\x02updated on\x03\x02 " + extractdate(whois["updatedDate"]).strftime("%c") + ", " if "updatedDate" in whois else "",
                                                             "\x03\x02expires on\x03\x02 " + extractdate(whois["expiresDate"]).strftime("%c") + ", " if "expiresDate" in whois else "",
                                                             whois_entityformat(whois["registrant"]) if "registrant" in whois else "unknown",
                                                             whois_entityformat(whois["administrativeContact"]) if "administrativeContact" in whois else "unknown",
                                                             whois_entityformat(whois["technicalContact"]) if "technicalContact" in whois else "unknown",
                                                         ))
    return res
