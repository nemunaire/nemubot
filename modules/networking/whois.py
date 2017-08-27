# PYTHON STUFFS #######################################################

import datetime
import urllib

from nemubot.exception import IMException
from nemubot.tools.web import getJSON

from nemubot.module.more import Response

URL_AVAIL = "https://www.whoisxmlapi.com/whoisserver/WhoisService?cmd=GET_DN_AVAILABILITY&domainName=%%s&outputFormat=json&username=%s&password=%s"
URL_WHOIS = "http://www.whoisxmlapi.com/whoisserver/WhoisService?da=2&domainName=%%s&outputFormat=json&userName=%s&password=%s"


# LOADING #############################################################

def load(CONF, add_hook):
    global URL_AVAIL, URL_WHOIS

    if not CONF or not CONF.hasNode("whoisxmlapi") or "username" not in CONF.getNode("whoisxmlapi") or "password" not in CONF.getNode("whoisxmlapi"):
        raise ImportError("You need a WhoisXML API account in order to use "
                          "the !netwhois feature. Add it to the module "
                          "configuration file:\n<whoisxmlapi username=\"XX\" "
                          "password=\"XXX\" />\nRegister at "
                          "http://www.whoisxmlapi.com/newaccount.php")

    URL_AVAIL = URL_AVAIL % (urllib.parse.quote(CONF.getNode("whoisxmlapi")["username"]), urllib.parse.quote(CONF.getNode("whoisxmlapi")["password"]))
    URL_WHOIS = URL_WHOIS % (urllib.parse.quote(CONF.getNode("whoisxmlapi")["username"]), urllib.parse.quote(CONF.getNode("whoisxmlapi")["password"]))

    import nemubot.hooks
    add_hook(nemubot.hooks.Command(cmd_whois, "netwhois",
                                   help="Get whois information about given domains",
                                   help_usage={"DOMAIN": "Return whois information on the given DOMAIN"}),
             "in","Command")
    add_hook(nemubot.hooks.Command(cmd_avail, "domain_available",
                                   help="Domain availability check using whoisxmlapi.com",
                                   help_usage={"DOMAIN": "Check if the given DOMAIN is available or not"}),
             "in","Command")


# MODULE CORE #########################################################

def whois_entityformat(entity):
    ret = ""
    if "organization" in entity:
        ret += entity["organization"]
    if "organization" in entity and "name" in entity:
        ret += " "
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

def available(dom):
    js = getJSON(URL_AVAIL % urllib.parse.quote(dom))

    if "ErrorMessage" in js:
        raise IMException(js["ErrorMessage"]["msg"])

    return js["DomainInfo"]["domainAvailability"] == "AVAILABLE"


# MODULE INTERFACE ####################################################

def cmd_avail(msg):
    if not len(msg.args):
        raise IMException("Indicate a domain name for having its availability status!")

    return Response(["%s: %s" % (dom, "available" if available(dom) else "unavailable") for dom in msg.args],
                    channel=msg.channel)


def cmd_whois(msg):
    if not len(msg.args):
        raise IMException("Indiquer un domaine ou une IP à whois !")

    dom = msg.args[0]

    js = getJSON(URL_WHOIS % urllib.parse.quote(dom))

    if "ErrorMessage" in js:
        raise IMException(js["ErrorMessage"]["msg"])

    whois = js["WhoisRecord"]

    res = []

    if "registrarName" in whois:
        res.append("\x03\x02registered by\x03\x02 " + whois["registrarName"])

    if "domainAvailability" in whois:
        res.append(whois["domainAvailability"])

    if "contactEmail" in whois:
        res.append("\x03\x02contact email\x03\x02 " + whois["contactEmail"])

    if "audit" in whois:
        if "createdDate" in whois["audit"] and "$" in whois["audit"]["createdDate"]:
            res.append("\x03\x02created on\x03\x02 " + whois["audit"]["createdDate"]["$"])
        if "updatedDate" in whois["audit"] and "$" in whois["audit"]["updatedDate"]:
            res.append("\x03\x02updated on\x03\x02 " + whois["audit"]["updatedDate"]["$"])

    if "registryData" in whois:
        if "expiresDateNormalized" in whois["registryData"]:
            res.append("\x03\x02expire on\x03\x02 " + whois["registryData"]["expiresDateNormalized"])
        if "registrant" in whois["registryData"]:
            res.append("\x03\x02registrant:\x03\x02 " + whois_entityformat(whois["registryData"]["registrant"]))
        if "zoneContact" in whois["registryData"]:
            res.append("\x03\x02zone contact:\x03\x02 " + whois_entityformat(whois["registryData"]["zoneContact"]))
        if "technicalContact" in whois["registryData"]:
            res.append("\x03\x02technical contact:\x03\x02 " + whois_entityformat(whois["registryData"]["technicalContact"]))
        if "administrativeContact" in whois["registryData"]:
            res.append("\x03\x02administrative contact:\x03\x02 " + whois_entityformat(whois["registryData"]["administrativeContact"]))
        if "billingContact" in whois["registryData"]:
            res.append("\x03\x02billing contact:\x03\x02 " + whois_entityformat(whois["registryData"]["billingContact"]))

    return Response(res,
                    title=whois["domainName"],
                    channel=msg.channel,
                    nomore="No more whois information")
