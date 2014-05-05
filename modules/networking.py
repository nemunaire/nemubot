# coding=utf-8

import datetime
import http.client
import json
import socket
import urllib

from tools import web

nemubotversion = 3.3

def load(context):
    from hooks import Hook

    if not CONF.hasNode("whoisxmlapi") or not CONF.getNode("whoisxmlapi").hasAttribute("username") or not CONF.getNode("whoisxmlapi").hasAttribute("password"):
        print ("You need a WhoisXML API account in order to use the "
               "!netwhois feature. Add it to the module configuration file:\n"
               "<whoisxmlapi username=\"XX\" password=\"XXX\" />\nRegister at "
               "http://www.whoisxmlapi.com/newaccount.php")
    else:
        add_hook("cmd_hook", Hook(cmd_whois, "netwhois"))

    add_hook("cmd_hook", Hook(cmd_traceurl, "traceurl"))
    add_hook("cmd_hook", Hook(cmd_isup, "isup"))
    add_hook("cmd_hook", Hook(cmd_curl, "curl"))


def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "The networking module"

def help_full ():
    return "!traceurl /url/: Follow redirections from /url/."

def cmd_curl(msg):
    if len(msg.cmds) > 1:
        try:
            req = web.getURLContent(" ".join(msg.cmds[1:]))
            if req is not None:
                res = Response(msg.sender, channel=msg.channel)
                for m in req.decode().split("\n"):
                    res.append_message(m)
                return res
            else:
                return Response(msg.sender, "Une erreur est survenue lors de l'accès à cette URL", channel=msg.channel)
        except socket.error as e:
            return Response(msg.sender, e.strerror, channel=msg.channel)
    else:
        return Response(msg.sender, "Veuillez indiquer une URL à visiter.",
                        channel=msg.channel)

def cmd_traceurl(msg):
    if 1 < len(msg.cmds) < 6:
        res = list()
        for url in msg.cmds[1:]:
            trace = traceURL(url)
            res.append(Response(msg.sender, trace, channel=msg.channel, title="TraceURL"))
        return res
    else:
        return Response(msg.sender, "Indiquer une URL à tracer !", channel=msg.channel)


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
        req = urllib.request.Request("http://www.whoisxmlapi.com/whoisserver/WhoisService?rid=1&domainName=%s&outputFormat=json&userName=%s&password=%s" % (urllib.parse.quote(dom), urllib.parse.quote(CONF.getNode("whoisxmlapi")["username"]), urllib.parse.quote(CONF.getNode("whoisxmlapi")["password"])), headers={ 'User-Agent' : "nemubot v3" })
        raw = urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as e:
        raise IRCException("HTTP error occurs: %s %s" % (e.code, e.reason))

    whois = json.loads(raw.read().decode())["WhoisRecord"]

    res = Response(msg.sender, channel=msg.channel, nomore="No more whois information")

    res.append_message("%s: %s%s%s%s\x03\x02registered by\x03\x02 %s, \x03\x02administrated by\x03\x02 %s, \x03\x02managed by\x03\x02 %s" % (whois["domainName"],
                                                             whois["status"] + " " if "status" in whois else "",
                                                             "\x03\x02created on\x03\x02 " + extractdate(whois["createdDate"]).strftime("%c") + ", " if "createdDate" in whois else "",
                                                             "\x03\x02updated on\x03\x02 " + extractdate(whois["updatedDate"]).strftime("%c") + ", " if "updatedDate" in whois else "",
                                                             "\x03\x02expires on\x03\x02 " + extractdate(whois["expiresDate"]).strftime("%c") + ", " if "expiresDate" in whois else "",
                                                             whois_entityformat(whois["registrant"]),
                                                             whois_entityformat(whois["administrativeContact"]),
                                                             whois_entityformat(whois["technicalContact"]),
                                                         ))
    return res

def cmd_isup(msg):
    if 1 < len(msg.cmds) < 6:
        res = list()
        for url in msg.cmds[1:]:
            o = urllib.parse.urlparse(url, "http")
            if o.netloc == "":
                o = urllib.parse.urlparse("http://" + url)
            if o.netloc != "":
                req = urllib.request.Request("http://isitup.org/%s.json" % (o.netloc), headers={ 'User-Agent' : "nemubot v3" })
                raw = urllib.request.urlopen(req, timeout=10)
                isup = json.loads(raw.read().decode())
                if "status_code" in isup and isup["status_code"] == 1:
                    res.append(Response(msg.sender, "%s est accessible (temps de reponse : %ss)" % (isup["domain"], isup["response_time"]), channel=msg.channel))
                else:
                    res.append(Response(msg.sender, "%s n'est pas accessible :(" % (isup["domain"]), channel=msg.channel))
            else:
                res.append(Response(msg.sender, "%s n'est pas une URL valide" % url, channel=msg.channel))
        return res
    else:
        return Response(msg.sender, "Indiquer une URL à vérifier !", channel=msg.channel)

def traceURL(url, timeout=5, stack=None):
    """Follow redirections and return the redirections stack"""
    if stack is None:
        stack = list()
    stack.append(url)

    if len(stack) > 15:
        stack.append('stack overflow :(')
        return stack

    o = urlparse(url, "http")
    if o.netloc == "":
        return stack
    if o.scheme == "http":
        conn = http.client.HTTPConnection(o.netloc, port=o.port, timeout=timeout)
    else:
        conn = http.client.HTTPSConnection(o.netloc, port=o.port, timeout=timeout)
    try:
        conn.request("HEAD", o.path, None, {"User-agent": "Nemubot v3"})
    except socket.timeout:
        stack.append("Timeout")
        return stack
    except socket.gaierror:
        print ("<tools.web> Unable to receive page %s from %s on %d."
               % (o.path, o.netloc, o.port))
        return stack

    try:
        res = conn.getresponse()
    except http.client.BadStatusLine:
        return stack
    finally:
        conn.close()

    if res.status == http.client.OK:
        return stack
    elif res.status == http.client.FOUND or res.status == http.client.MOVED_PERMANENTLY or res.status == http.client.SEE_OTHER:
        url = res.getheader("Location")
        if url in stack:
            stack.append("loop on " + url)
            return stack
        else:
            return traceURL(url, timeout, stack)
    else:
        return stack
