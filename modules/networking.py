# coding=utf-8

import datetime
import http.client
import json
import socket
import subprocess
import urllib

from tools import web

nemubotversion = 3.3

def load(context):
    from hooks import Hook

    if not CONF or not CONF.hasNode("whoisxmlapi") or not CONF.getNode("whoisxmlapi").hasAttribute("username") or not CONF.getNode("whoisxmlapi").hasAttribute("password"):
        print ("You need a WhoisXML API account in order to use the "
               "!netwhois feature. Add it to the module configuration file:\n"
               "<whoisxmlapi username=\"XX\" password=\"XXX\" />\nRegister at "
               "http://www.whoisxmlapi.com/newaccount.php")
    else:
        add_hook("cmd_hook", Hook(cmd_whois, "netwhois"))

    add_hook("cmd_hook", Hook(cmd_w3c, "w3c"))
    add_hook("cmd_hook", Hook(cmd_w3m, "w3m"))
    add_hook("cmd_hook", Hook(cmd_traceurl, "traceurl"))
    add_hook("cmd_hook", Hook(cmd_isup, "isup"))
    add_hook("cmd_hook", Hook(cmd_curl, "curl"))
    add_hook("cmd_hook", Hook(cmd_curly, "curly"))


def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "The networking module"

def help_full ():
    return "!traceurl /url/: Follow redirections from /url/."

def cmd_w3m(msg):
    if len(msg.cmds) > 1:
        args = ["w3m", "-T", "text/html", "-dump"]
        args.append(msg.cmds[1])
        res = Response(msg.sender, channel=msg.channel)
        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            for line in proc.stdout.read().split(b"\n"):
                res.append_message(line.decode())
        return res
    else:
        raise IRCException("Veuillez indiquer une URL à visiter.")

def cmd_curl(msg):
    if len(msg.cmds) > 1:
        try:
            req = web.getURLContent(" ".join(msg.cmds[1:]))
            if req is not None:
                res = Response(msg.sender, channel=msg.channel)
                for m in req.split("\n"):
                    res.append_message(m)
                return res
            else:
                return Response(msg.sender, "Une erreur est survenue lors de l'accès à cette URL", channel=msg.channel)
        except socket.timeout:
            return Response(msg.sender, "le délais d'attente a été dépassé durant l'accès à %s" % msg.cmds[1:], channel=msg.channel, nick=msg.nick)
        except socket.error as e:
            return Response(msg.sender, e.strerror, channel=msg.channel)
    else:
        return Response(msg.sender, "Veuillez indiquer une URL à visiter.",
                        channel=msg.channel)

def cmd_curly(msg):
    if len(msg.cmds) > 1:
        url = msg.cmds[1]
        o = urllib.parse.urlparse(url, "http")
        if o.netloc == "":
            raise IRCException("URL invalide")
        if o.scheme == "http":
            conn = http.client.HTTPConnection(o.netloc, port=o.port, timeout=5)
        else:
            conn = http.client.HTTPSConnection(o.netloc, port=o.port, timeout=5)
        try:
            conn.request("HEAD", o.path, None, {"User-agent": "Nemubot v3"})
        except socket.timeout:
            raise IRCException("Délais d'attente dépassé")
        except socket.gaierror:
            print ("<tools.web> Unable to receive page %s from %s on %d."
                   % (o.path, o.netloc, o.port))
            raise IRCException("Une erreur innatendue est survenue")

        try:
            res = conn.getresponse()
        except http.client.BadStatusLine:
            raise IRCException("Une erreur est survenue")
        finally:
            conn.close()

        return Response(msg.sender, "Entêtes de la page %s : HTTP/%s, statut : %d %s ; headers : %s" % (url, res.version, res.status, res.reason, ", ".join(["\x03\x02" + h + "\x03\x02: " + v for h, v in res.getheaders()])), channel=msg.channel)
    else:
        raise IRCException("Veuillez indiquer une URL à visiter.")

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
    except socket.timeout:
        raise IRCException("Sorry, the request has timed out.")
    except urllib.error.HTTPError as e:
        raise IRCException("HTTP error occurs: %s %s" % (e.code, e.reason))

    js = json.loads(raw.read().decode())

    if "ErrorMessage" in js:
        err = js["ErrorMessage"]
        raise IRCException(js["ErrorMessage"]["msg"])

    whois = js["WhoisRecord"]

    res = Response(msg.sender, channel=msg.channel, nomore="No more whois information")

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

    o = urllib.parse.urlparse(url, "http")
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

def cmd_w3c(msg):
    if len(msg.cmds) < 2:
        raise IRCException("Indiquer une URL à valider !")

    o = urllib.parse.urlparse(msg.cmds[1], "http")
    if o.netloc == "":
        o = urllib.parse.urlparse("http://" + msg.cmds[1])
    if o.netloc == "":
        raise IRCException("Indiquer une URL valide !")

    try:
        req = urllib.request.Request("http://validator.w3.org/check?uri=%s&output=json" % (urllib.parse.quote(o.geturl())), headers={ 'User-Agent' : "nemubot v3" })
        raw = urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as e:
        raise IRCException("HTTP error occurs: %s %s" % (e.code, e.reason))

    headers = dict()
    for Hname, Hval in raw.getheaders():
        headers[Hname] = Hval

    if "X-W3C-Validator-Status" not in headers or (headers["X-W3C-Validator-Status"] != "Valid" and headers["X-W3C-Validator-Status"] != "Invalid"):
        raise IRCException("Unexpected error on W3C servers" + (" (" + headers["X-W3C-Validator-Status"] + ")" if "X-W3C-Validator-Status" in headers else ""))

    validator = json.loads(raw.read().decode())

    res = Response(msg.sender, channel=msg.channel, nomore="No more error")

    res.append_message("%s: status: %s, %s warning(s), %s error(s)" % (validator["url"], headers["X-W3C-Validator-Status"], headers["X-W3C-Validator-Warnings"], headers["X-W3C-Validator-Errors"]))

    for m in validator["messages"]:
        res.append_message("%s%s on line %s, col %s: %s" % (m["type"][0].upper(), m["type"][1:], m["lastLine"], m["lastColumn"], m["message"]))

    return res
