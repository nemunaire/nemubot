# coding=utf-8

import json
import re

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools.xmlparser.node import ModuleState

nemubotversion = 3.4

from more import Response
from networking.page import headers

PASSWD_FILE = None
# You can get one with: curl -b "sessionid=YOURSESSIONID" 'https://accounts.cri.epita.net/api/users/' > users.json
APIEXTRACT_FILE = None

def load(context):
    global PASSWD_FILE
    if not context.config or "passwd" not in context.config:
        print("No passwd file given")
    else:
        PASSWD_FILE = context.config["passwd"]
        print("passwd file loaded:", PASSWD_FILE)

    global APIEXTRACT_FILE
    if not context.config or "apiextract" not in context.config:
        print("No passwd file given")
    else:
        APIEXTRACT_FILE = context.config["apiextract"]
        print("JSON users file loaded:", APIEXTRACT_FILE)

    if PASSWD_FILE is None and APIEXTRACT_FILE is None:
        return None

    if not context.data.hasNode("aliases"):
        context.data.addChild(ModuleState("aliases"))
    context.data.getNode("aliases").setIndex("from", "alias")

    if not context.data.hasNode("pics"):
        context.data.addChild(ModuleState("pics"))
    context.data.getNode("pics").setIndex("login", "pict")

    import nemubot.hooks
    context.add_hook(nemubot.hooks.Command(cmd_whois, "whois", keywords={"lookup": "Perform a lookup of the begining of the login instead of an exact search."}),
                     "in","Command")

class Login:

    def __init__(self, line=None, login=None, uidNumber=None, cn=None, promo=None, **kwargs):
        if line is not None:
            s = line.split(":")
            self.login = s[0]
            self.uid = s[2]
            self.gid = s[3]
            self.cn = s[4]
            self.home = s[5]
        else:
            self.login = login
            self.uid = uidNumber
            self.promo = promo
            self.cn = cn
            self.gid = "epita" + promo

    def get_promo(self):
        if hasattr(self, "promo"):
            return self.promo
        if hasattr(self, "home"):
            return self.home.split("/")[2].replace("_", " ")

    def get_photo(self):
        if self.login in context.data.getNode("pics").index:
            return context.data.getNode("pics").index[self.login]["url"]
        for url in [ "https://photos.cri.epita.net/%s", "https://static.acu.epita.fr/photos/%s", "https://static.acu.epita.fr/photos/%s/%%s" % self.gid, "https://intra-bocal.epitech.eu/trombi/%s.jpg", "http://whois.23.tf/p/%s/%%s.jpg" % self.gid ]:
            url = url % self.login
            try:
                _, status, _, _ = headers(url)
                if status == 200:
                    return url
            except:
                logger.exception("On URL %s", url)
        return None


def login_lookup(login, search=False):
    if login in context.data.getNode("aliases").index:
        login = context.data.getNode("aliases").index[login]["to"]

    if APIEXTRACT_FILE:
        with open(APIEXTRACT_FILE, encoding="utf-8") as f:
            api = json.load(f)
            for l in api:
                if (not search and l["login"] == login) or (search and (("login" in l and l["login"].find(login) != -1) or ("cn" in l and l["cn"].find(login) != -1) or ("uid" in l and str(l["uid"]) == login))):
                    yield Login(**l)

    login_ = login + (":" if not search else "")
    lsize = len(login_)

    if PASSWD_FILE:
        with open(PASSWD_FILE, encoding="iso-8859-15") as f:
            for l in f.readlines():
                if l[:lsize] == login_:
                    yield Login(l.strip())

def cmd_whois(msg):
    if len(msg.args) < 1:
        raise IMException("Provide a name")

    def format_response(t):
        srch, l = t
        if type(l) is Login:
            pic = l.get_photo()
            return "%s is %s (%s %s): %s%s" % (srch, l.cn.capitalize(), l.login, l.uid, l.get_promo(), " and looks like %s" % pic if pic is not None else "")
        else:
            return l % srch

    res = Response(channel=msg.channel, count=" (%d more logins)", line_treat=format_response)
    for srch in msg.args:
        found = False
        for l in login_lookup(srch, "lookup" in msg.kwargs):
            found = True
            res.append_message((srch, l))
        if not found:
            res.append_message((srch, "Unknown %s :("))
    return res

@hook.command("nicks")
def cmd_nicks(msg):
    if len(msg.args) < 1:
        raise IMException("Provide a login")
    nick = login_lookup(msg.args[0])
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

@hook.ask()
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
