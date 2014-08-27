# coding=utf-8

"""Send SMS using SMS API (currently only Free Mobile)"""

import re
import socket
import time
import urllib.error
import urllib.request
import urllib.parse

from hooks import hook

nemubotversion = 3.4

def load(context):
    global DATAS
    DATAS.setIndex("name", "phone")

def help_full():
    return "!sms /who/[,/who/[,...]] message: send a SMS to /who/."

def send_sms(frm, api_usr, api_key, content):
    content = "<%s> %s" % (frm, content)

    try:
        req = urllib.request.Request("https://smsapi.free-mobile.fr/sendmsg?user=%s&pass=%s&msg=%s" % (api_usr, api_key, urllib.parse.quote(content)))
        res = urllib.request.urlopen(req, timeout=5)
    except socket.timeout:
        return "timeout"
    except urllib.error.HTTPError as e:
        if e.code == 400:
            return "paramètre manquant"
        elif e.code == 402:
            return "paiement requis"
        elif e.code == 403 or e.code == 404:
            return "clef incorrecte"
        elif e.code != 200:
            return "erreur inconnue (%d)" % status
    except:
        return "unknown error"

    return None


@hook("cmd_hook", "sms")
def cmd_sms(msg):
    if len(msg.cmds) <= 2:
        raise IRCException("À qui veux-tu envoyer ce SMS ?")

    # Check dests
    cur_epoch = time.mktime(time.localtime());
    for u in msg.cmds[1].split(","):
        if u not in DATAS.index:
            raise IRCException("Désolé, je sais pas comment envoyer de SMS à %s." % u)
        elif cur_epoch - float(DATAS.index[u]["lastuse"]) < 42:
            raise IRCException("Un peu de calme, %s a déjà reçu un SMS il n'y a pas si longtemps." % u)

    # Go!
    fails = list()
    for u in msg.cmds[1].split(","):
        DATAS.index[u]["lastuse"] = cur_epoch
        if msg.private:
            frm = msg.nick
        else:
            frm = msg.nick + "@" + msg.channel
        test = send_sms(frm, DATAS.index[u]["user"], DATAS.index[u]["key"], " ".join(msg.cmds[2:]))
        if test is not None:
            fails.append( "%s: %s" % (u, test) )

    if len(fails) > 0:
        return Response(msg.sender, "quelque chose ne s'est pas bien passé durant l'envoi du SMS : " + ", ".join(fails), msg.channel, msg.nick)
    else:
        return Response(msg.sender, "le SMS a bien été envoyé", msg.channel, msg.nick)

apiuser_ask = re.compile(r"(utilisateur|user|numéro|numero|compte|abonne|abone|abonné|account)\s+(est|is)\s+(?P<user>[0-9]{7,})", re.IGNORECASE)
apikey_ask = re.compile(r"(clef|key|password|mot de passe?)\s+(?:est|is)?\s+(?P<key>[a-zA-Z0-9]{10,})", re.IGNORECASE)

def parseask(msg):
    if msg.content.find("Free") >= 0 and (
            msg.content.find("API") >= 0 or msg.content.find("api") >= 0) and (
                msg.content.find("SMS") >= 0 or msg.content.find("sms") >= 0):
        resuser = apiuser_ask.search(msg.content)
        reskey = apikey_ask.search(msg.content)
        if resuser is not None and reskey is not None:
            apiuser = resuser.group("user")
            apikey = reskey.group("key")

            test = send_sms("nemubot", apiuser, apikey,
                            "Vous avez enregistré vos codes d'authentification dans nemubot, félicitation !")
            if test is not None:
                return Response(msg.sender, "je n'ai pas pu enregistrer tes identifiants : %s" % test, msg.channel, msg.nick)

            if msg.nick in DATAS.index:
                DATAS.index[msg.nick]["user"] = apiuser
                DATAS.index[msg.nick]["key"] = apikey
            else:
                ms = ModuleState("phone")
                ms.setAttribute("name", msg.nick)
                ms.setAttribute("user", apiuser)
                ms.setAttribute("key", apikey)
                ms.setAttribute("lastuse", 0)
                DATAS.addChild(ms)
            save()
            return Response(msg.sender, "ok, c'est noté. Je t'ai envoyé un SMS pour tester ;)",
                            msg.channel, msg.nick)
