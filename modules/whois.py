# coding=utf-8

import re

from nemubot import context
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools.xmlparser.node import ModuleState

nemubotversion = 3.4

from more import Response
from networking.page import headers

PASSWD_FILE = None

def load(context):
    global PASSWD_FILE
    if not context.config or "passwd" not in context.config:
        print("No passwd file given")
        return None
    PASSWD_FILE = context.config["passwd"]

    if not context.data.hasNode("aliases"):
        context.data.addChild(ModuleState("aliases"))
    context.data.getNode("aliases").setIndex("from", "alias")

    if not context.data.hasNode("pics"):
        context.data.addChild(ModuleState("pics"))
    context.data.getNode("pics").setIndex("login", "pict")

    import nemubot.hooks
    context.add_hook("cmd_hook",
                     nemubot.hooks.Message(cmd_whois, "whois"))

class Login:

    def __init__(self, line):
        s = line.split(":")
        self.login = s[0]
        self.uid = s[2]
        self.gid = s[3]
        self.cn = s[4]
        self.home = s[5]

    def get_promo(self):
        return self.home.split("/")[2].replace("_", " ")

    def get_photo(self):
        if self.login in context.data.getNode("pics").index:
            return context.data.getNode("pics").index[self.login]["url"]
        for url in [ "https://static.acu.epita.fr/photos/%s", "https://static.acu.epita.fr/photos/%s/%%s" % self.gid, "https://intra-bocal.epitech.eu/trombi/%s.jpg", "http://whois.23.tf/p/%s/%%s.jpg" % self.gid ]:
            url = url % self.login
            try:
                _, status, _, _ = headers(url)
                if status == 200:
                    return url
            except:
                logger.exception("On URL %s", url)
        return None


def found_login(login):
    if login in context.data.getNode("aliases").index:
        login = context.data.getNode("aliases").index[login]["to"]

    login_ = login + ":"
    lsize = len(login_)

    with open(PASSWD_FILE, encoding="iso-8859-15") as f:
        for l in f.readlines():
            if l[:lsize] == login_:
                return Login(l.strip())
    return None

def cmd_whois(msg):
    if len(msg.args) < 1:
        raise IRCException("Provide a name")

    res = Response(channel=msg.channel, count=" (%d more logins)")
    for srch in msg.args:
        l = found_login(srch)
        if l is not None:
            pic = l.get_photo()
            res.append_message("%s is %s (%s %s): %s%s" % (srch, l.cn.capitalize(), l.login, l.uid, l.get_promo(), " and looks like %s" % pic if pic is not None else ""))
        else:
            res.append_message("Unknown %s :(" % srch)
    return res

@hook("cmd_hook", "nicks")
def cmd_nicks(msg):
    if len(msg.args) < 1:
        raise IRCException("Provide a login")
    nick = found_login(msg.args[0])
    if nick is None:
        nick = msg.args[0]
    else:
        nick = nick.login

    nicks = []
    for alias in context.data.getNode("aliases").getChilds():
        if alias["to"] == nick:
            nicks.append(alias["from"])
    if len(nicks) >= 1:
        return Response("%s is also known as %s." % (nick, ", ".join(nicks)), channel=msg.channel)
    else:
        return Response("%s has no known alias." % nick, channel=msg.channel)

@hook("ask_default")
def parseask(msg):
    res = re.match(r"^(\S+)\s*('s|suis|est|is|was|were)\s+([a-zA-Z0-9_-]{3,8})$", msg.text, re.I)
    if res is not None:
        nick = res.group(1)
        login = res.group(3)
        if nick == "my" or nick == "I" or nick == "i" or nick == "je" or nick == "mon" or nick == "ma":
            nick = msg.nick
        if nick in context.data.getNode("aliases").index:
            context.data.getNode("aliases").index[nick]["to"] = login
        else:
            ms = ModuleState("alias")
            ms.setAttribute("from", nick)
            ms.setAttribute("to", login)
            context.data.getNode("aliases").addChild(ms)
        context.save()
        return Response("ok, c'est noté, %s est %s"
                        % (nick, login),
                        channel=msg.channel,
                        nick=msg.nick)
