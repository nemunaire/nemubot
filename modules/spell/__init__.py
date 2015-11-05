"""Check words spelling"""

# PYTHON STUFFS #######################################################

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools.xmlparser.node import ModuleState

from .pyaspell import Aspell
from .pyaspell import AspellError

from more import Response


# LOADING #############################################################

def load(context):
    context.data.setIndex("name", "score")


# MODULE CORE #########################################################

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


def check_spell(word, lang='fr'):
    a = Aspell([("lang", lang)])
    if a.check(word.encode("utf-8")):
        ret = True
    else:
        ret = a.suggest(word.encode("utf-8"))
    a.close()
    return ret


# MODULE INTERFACE ####################################################

@hook.command("spell",
              help="give the correct spelling of given words",
              help_usage={"WORD": "give the correct spelling of the WORD."},
              keywords={"lang=": "change the language use for checking, default fr"})
def cmd_spell(msg):
    if not len(msg.args):
        raise IMException("indique une orthographe approximative du mot dont tu veux vérifier l'orthographe.")

    lang = msg.kwargs["lang"] if "lang" in msg.kwargs else "fr"

    res = Response(channel=msg.channel)
    for word in msg.args:
        try:
            r = check_spell(word, lang)
        except AspellError:
            raise IMException("Je n'ai pas le dictionnaire `%s' :(" % lang)

        if r == True:
            add_score(msg.nick, "correct")
            res.append_message("l'orthographe de `%s' est correcte" % word)

        elif len(r) > 0:
            add_score(msg.nick, "bad")
            res.append_message(r, title="suggestions pour `%s'" % word)

        else:
            add_score(msg.nick, "bad")
            res.append_message("aucune suggestion pour `%s'" % word)

    return res


@hook.command("spellscore",
              help="Show spell score (tests, mistakes, ...) for someone",
              help_usage={"USER": "Display score of USER"})
def cmd_score(msg):
    res = list()
    unknown = list()
    if not len(msg.args):
        raise IMException("De qui veux-tu voir les scores ?")
    for cmd in msg.args:
        if cmd in context.data.index:
            res.append(Response("%s: %s" % (cmd, " ; ".join(["%s: %d" % (a, context.data.index[cmd].getInt(a)) for a in context.data.index[cmd].attributes.keys() if a != "name"])), channel=msg.channel))
        else:
            unknown.append(cmd)
    if len(unknown) > 0:
        res.append(Response("%s inconnus" % ", ".join(unknown), channel=msg.channel))

    return res
