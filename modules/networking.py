# coding=utf-8

from tools import web

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
            if web.isURL(url):
                trace = web.traceURL(url)
                res.append(Response(msg.sender, trace, channel=msg.channel, title="TraceURL"))
            else:
                res.append(Response(msg.sender, "%s n'est pas une URL valide" % url, channel=msg.channel))
        return res
    else:
        return Response(msg.sender, "Indiquer une URL a tracer !", channel=msg.channel)

def cmd_isup(msg):
    if 1 < len(msg.cmds) < 6:
        res = list()
        for url in msg.cmds[1:]:
            host = web.getHost(url)
            if host is not None:
                isup = web.getJSON("http://isitup.org/" + host + ".json")
                if "status_code" in isup and isup["status_code"] == 1:
                    res.append(Response(msg.sender, "%s est accessible (temps de reponse : %ss)" % (isup["domain"], isup["response_time"]), channel=msg.channel))
                else:
                    res.append(Response(msg.sender, "%s n'est pas accessible :(" % (isup["domain"]), channel=msg.channel))
            else:
                res.append(Response(msg.sender, "%s n'est pas une URL valide" % url, channel=msg.channel))
        return res
    else:
        return Response(msg.sender, "Indiquer une URL a verifier !", channel=msg.channel)
