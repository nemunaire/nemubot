# coding=utf-8

import re
from urllib.parse import quote

from .pyaspell import Aspell
from .pyaspell import AspellError

nemubotversion = 3.3

def help_tiny ():
  return "Check words spelling"

def help_full ():
  return "!spell [<lang>] <word>: give the correct spelling of <word> in <lang=fr>."

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_spell, "spell"))
    add_hook("cmd_hook", Hook(cmd_spell, "orthographe"))


def cmd_spell(msg):
    if len(msg.cmds) < 2:
        return Response(msg.sender, "Indiquer une orthographe approximative du mot dont vous voulez vérifier l'orthographe.", msg.channel)

    lang = "fr"
    strRes = list()
    for word in msg.cmds[1:]:
        if len(word) <= 2 and len(msg.cmds) > 2:
            lang = word
        else:
            try:
                r = check_spell(word, lang)
            except AspellError:
                return Response(msg.sender, "Je n'ai pas le dictionnaire `%s' :(" % lang, msg.channel)
            if r == True:
                strRes.append("l'orthographe de `%s' est correcte" % word)
            elif len(r) > 0:
                strRes.append("suggestions pour `%s' : %s" % (word, ", ".join(r)))
            else:
                strRes.append("aucune suggestion pour `%s'" % word)
    return Response(msg.sender, strRes, channel=msg.channel)

def check_spell(word, lang='fr'):
    a = Aspell(("lang", lang))
    if a.check(word):
        ret = True
    else:
        ret = a.suggest(word)
    a.close()
    return ret
