import datetime
import json
import socket
import urllib

from more import Response

URL_WHOIS = "http://www.whoisxmlapi.com/whoisserver/WhoisService?rid=1&domainName=%%s&outputFormat=json&userName=%s&password=%s"

def load(CONF, add_hook):
    global URL_WHOIS

    if not CONF or not CONF.hasNode("whoisxmlapi") or not CONF.getNode("whoisxmlapi").hasAttribute("username") or not CONF.getNode("whoisxmlapi").hasAttribute("password"):
        print ("You need a WhoisXML API account in order to use the "
               "!netwhois feature. Add it to the module configuration file:\n"
               "<whoisxmlapi username=\"XX\" password=\"XXX\" />\nRegister at "
               "http://www.whoisxmlapi.com/newaccount.php")
    else:
        URL_WHOIS = URL_WHOIS % (urllib.parse.quote(CONF.getNode("whoisxmlapi")["username"]), urllib.parse.quote(CONF.getNode("whoisxmlapi")["password"]))

        from hooks.messagehook import MessageHook
        add_hook("cmd_hook", MessageHook(cmd_whois, "netwhois"))


def extractdate(str):
    tries = [
        "%Y-%m-%dT%H:%M:%S%Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S%Z",
        "%Y-%m-%d %H:%M:%S%z",
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
    if len(msg.cmds) < 2:
        raise IRCException("Indiquer un domaine ou une IP à whois !")

    dom = msg.cmds[1]

    try:
        req = urllib.request.Request(URL_WHOIS % urllib.parse.quote(dom), headers={ 'User-Agent' : "nemubot v3" })
        raw = urllib.request.urlopen(req, timeout=10)
    except socket.timeout:
        raise IRCException("Sorry, the request has timed out.")
    except urllib.error.HTTPError as e:
        raise IRCException("HTTP error occurs: %s %s" % (e.code, e.reason))

    js = json.loads(raw.read().decode())

    if "ErrorMessage" in js:
        err = js["ErrorMessage"]
        raise IRCException(js["ErrorMessage"]["msg"])

    whois = js["WhoisRecord"]

    res = Response(channel=msg.channel, nomore="No more whois information")

    res.append_message("%s: %s%s%s%s\x03\x02registered by\x03\x02 %s, \x03\x02administrated by\x03\x02 %s, \x03\x02managed by\x03\x02 %s" % (whois["domainName"],
                                                             whois["status"] + " " if "status" in whois else "",
                                                             "\x03\x02created on\x03\x02 " + extractdate(whois["createdDate"]).strftime("%c") + ", " if "createdDate" in whois else "",
                                                             "\x03\x02updated on\x03\x02 " + extractdate(whois["updatedDate"]).strftime("%c") + ", " if "updatedDate" in whois else "",
                                                             "\x03\x02expires on\x03\x02 " + extractdate(whois["expiresDate"]).strftime("%c") + ", " if "expiresDate" in whois else "",
                                                             whois_entityformat(whois["registrant"]) if "registrant" in whois else "unknown",
                                                             whois_entityformat(whois["administrativeContact"]) if "administrativeContact" in whois else "unknown",
                                                             whois_entityformat(whois["technicalContact"]) if "technicalContact" in whois else "unknown",
                                                         ))
    return res
