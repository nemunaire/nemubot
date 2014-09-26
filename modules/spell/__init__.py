# coding=utf-8

"""Check words spelling"""

import re
from urllib.parse import quote

from hooks import hook

from .pyaspell import Aspell
from .pyaspell import AspellError

nemubotversion = 3.4

from more import Response

def help_full():
  return "!spell [<lang>] <word>: give the correct spelling of <word> in <lang=fr>."

def load(context):
    global DATAS
    DATAS.setIndex("name", "score")

@hook("cmd_hook", "spell")
def cmd_spell(msg):
    if len(msg.cmds) < 2:
        raise IRCException("indique une orthographe approximative du mot dont tu veux vérifier l'orthographe.")

    lang = "fr"
    strRes = list()
    for word in msg.cmds[1:]:
        if len(word) <= 2 and len(msg.cmds) > 2:
            lang = word
        else:
            try:
                r = check_spell(word, lang)
            except AspellError:
                return Response("Je n'ai pas le dictionnaire `%s' :(" % lang, msg.channel, msg.nick)
            if r == True:
                add_score(msg.nick, "correct")
                strRes.append("l'orthographe de `%s' est correcte" % word)
            elif len(r) > 0:
                add_score(msg.nick, "bad")
                strRes.append("suggestions pour `%s' : %s" % (word, ", ".join(r)))
            else:
                add_score(msg.nick, "bad")
                strRes.append("aucune suggestion pour `%s'" % word)
    return Response(strRes, channel=msg.channel, nick=msg.nick)

def add_score(nick, t):
    global DATAS
    if nick not in DATAS.index:
        st = ModuleState("score")
        st["name"] = nick
        DATAS.addChild(st)

    if DATAS.index[nick].hasAttribute(t):
        DATAS.index[nick][t] = DATAS.index[nick].getInt(t) + 1
    else:
        DATAS.index[nick][t] = 1
    save()

@hook("cmd_hook", "spellscore")
def cmd_score(msg):
    global DATAS
    res = list()
    unknown = list()
    if len(msg.cmds) > 1:
        for cmd in msg.cmds[1:]:
            if cmd in DATAS.index:
                res.append(Response("%s: %s" % (cmd, " ; ".join(["%s: %d" % (a, DATAS.index[cmd].getInt(a)) for a in DATAS.index[cmd].attributes.keys() if a != "name"])), channel=msg.channel))
            else:
                unknown.append(cmd)
    else:
        return Response("De qui veux-tu voir les scores ?", channel=msg.channel, nick=msg.nick)
    if len(unknown) > 0:
        res.append(Response("%s inconnus" % ", ".join(unknown), channel=msg.channel))

    return res

def check_spell(word, lang='fr'):
    a = Aspell([("lang", lang)])
    if a.check(word.encode("utf-8")):
        ret = True
    else:
        ret = a.suggest(word.encode("utf-8"))
    a.close()
    return ret
