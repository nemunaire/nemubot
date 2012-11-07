# coding=utf-8

import http.client
import json
from urllib.parse import urlparse
from urllib.request import urlopen

nemubotversion = 3.3

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_traceurl, "traceurl"))
    add_hook("cmd_hook", Hook(cmd_isup, "isup"))


def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "The networking module"

def help_full ():
    return "!traceurl /url/: Follow redirections from /url/."

def cmd_traceurl(msg):
    if 1 < len(msg.cmds) < 6:
        res = list()
        for url in msg.cmds[1:]:
            trace = traceURL(url)
            res.append(Response(msg.sender, trace, channel=msg.channel, title="TraceURL"))
        return res
    else:
        return Response(msg.sender, "Indiquer une URL a tracer !", channel=msg.channel)

def cmd_isup(msg):
    if 1 < len(msg.cmds) < 6:
        res = list()
        for url in msg.cmds[1:]:
            o = urlparse(url, "http")
            if o.netloc == "":
                o = urlparse("http://" + url)
            if o.netloc != "":
                raw = urlopen("http://isitup.org/" + o.netloc + ".json", timeout=10)
                isup = json.loads(raw.read().decode())
                if "status_code" in isup and isup["status_code"] == 1:
                    res.append(Response(msg.sender, "%s est accessible (temps de reponse : %ss)" % (isup["domain"], isup["response_time"]), channel=msg.channel))
                else:
                    res.append(Response(msg.sender, "%s n'est pas accessible :(" % (isup["domain"]), channel=msg.channel))
            else:
                res.append(Response(msg.sender, "%s n'est pas une URL valide" % url, channel=msg.channel))
        return res
    else:
        return Response(msg.sender, "Indiquer une URL a verifier !", channel=msg.channel)


def traceURL(url, timeout=5, stack=None):
    """Follow redirections and return the redirections stack"""
    if stack is None:
        stack = list()
    stack.append(url)

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
        return None

    try:
        res = conn.getresponse()
    except http.client.BadStatusLine:
        return None
    finally:
        conn.close()

    if res.status == http.client.OK:
        return stack
    elif res.status == http.client.FOUND or res.status == http.client.MOVED_PERMANENTLY or res.status == http.client.SEE_OTHER:
        url = res.getheader("Location")
        if url in stack:
            stack.append(url)
            return stack
        else:
            return traceURL(url, timeout, stack)
    else:
        return None
