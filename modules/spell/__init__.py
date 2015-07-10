# coding=utf-8

"""Check words spelling"""

import re
from urllib.parse import quote

from nemubot import context
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools.xmlparser.node import ModuleState

from .pyaspell import Aspell
from .pyaspell import AspellError

nemubotversion = 3.4

from more import Response

def help_full():
  return "!spell [<lang>] <word>: give the correct spelling of <word> in <lang=fr>."

def load(context):
    context.data.setIndex("name", "score")

@hook("cmd_hook", "spell")
def cmd_spell(msg):
    if not len(msg.args):
        raise IRCException("indique une orthographe approximative du mot dont tu veux vérifier l'orthographe.")

    lang = "fr"
    strRes = list()
    for word in msg.args:
        if len(word) <= 2 and len(msg.args) > 2:
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
    if nick not in context.data.index:
        st = ModuleState("score")
        st["name"] = nick
        context.data.addChild(st)

    if context.data.index[nick].hasAttribute(t):
        context.data.index[nick][t] = context.data.index[nick].getInt(t) + 1
    else:
        context.data.index[nick][t] = 1
    context.save()

@hook("cmd_hook", "spellscore")
def cmd_score(msg):
    res = list()
    unknown = list()
    if not len(msg.args):
        raise IRCException("De qui veux-tu voir les scores ?")
    for cmd in msg.args:
        if cmd in context.data.index:
            res.append(Response("%s: %s" % (cmd, " ; ".join(["%s: %d" % (a, context.data.index[cmd].getInt(a)) for a in context.data.index[cmd].attributes.keys() if a != "name"])), channel=msg.channel))
        else:
            unknown.append(cmd)
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
