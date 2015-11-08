"""Find synonyms"""

# PYTHON STUFFS #######################################################

import re
from urllib.parse import quote

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response


# LOADING #############################################################

def load(context):
    global lang_binding

    if not context.config or not "bighugelabskey" in context.config:
        logger.error("You need a NigHugeLabs API key in order to have english "
                     "theasorus. Add it to the module configuration file:\n"
                     "<module name=\"syno\" bighugelabskey=\"XXXXXXXXXXXXXXXX\""
                     " />\nRegister at https://words.bighugelabs.com/getkey.php")
    else:
        lang_binding["en"] = lambda word: get_english_synos(context.config["bighugelabskey"], word)


# MODULE CORE #########################################################

def get_french_synos(word):
    url = "http://www.crisco.unicaen.fr/des/synonymes/" + quote(word.encode("ISO-8859-1"))
    page = web.getURLContent(url)

    best = list(); synos = list(); anton = list()

    if page is not None:
        for line in page.split("\n"):

            if line.find("!-- Fin liste des antonymes --") > 0:
                for elt in re.finditer(">([^<>]+)</a>", line):
                    anton.append(elt.group(1))

            elif line.find("!--Fin liste des synonymes--") > 0:
                for elt in re.finditer(">([^<>]+)</a>", line):
                    synos.append(elt.group(1))

            elif re.match("[ \t]*<tr[^>]*>.*</tr>[ \t]*</table>.*", line) is not None:
                for elt in re.finditer(">&[^;]+;([^&]*)&[^;]+;<", line):
                    best.append(elt.group(1))

    return (best, synos, anton)


def get_english_synos(key, word):
    cnt = web.getJSON("http://words.bighugelabs.com/api/2/%s/%s/json" %
                      (quote(key), quote(word.encode("ISO-8859-1"))))

    best = list(); synos = list(); anton = list()

    if cnt is not None:
        for k, c in cnt.items():
            if "syn" in c: best += c["syn"]
            if "rel" in c: synos += c["rel"]
            if "ant" in c: anton += c["ant"]

    return (best, synos, anton)


lang_binding = { 'fr': get_french_synos }


# MODULE INTERFACE ####################################################

@hook.command("synonymes", data="synonymes",
              help="give a list of synonyms",
              help_usage={"WORD": "give synonyms of the given WORD"},
              keywords={
                  "lang=LANG": "change the dictionnary language: default fr, available: " + ", ".join(lang_binding)
              })
@hook.command("antonymes", data="antonymes",
              help="give a list of antonyms",
              help_usage={"WORD": "give antonyms of the given WORD"},
              keywords={
                  "lang=LANG": "change the dictionnary language: default fr, available: " + ", ".join(lang_binding)
              })
def go(msg, what):
    if not len(msg.args):
        raise IMException("de quel mot veux-tu connaître la liste des synonymes ?")

    lang = msg.kwargs["lang"] if "lang" in msg.kwargs else "fr"
    word = ' '.join(msg.args)

    try:
        best, synos, anton = lang_binding[lang](word)
    except:
        best, synos, anton = (list(), list(), list())

    if what == "synonymes":
        if len(synos) > 0 or len(best) > 0:
            res = Response(channel=msg.channel, title="Synonymes de %s" % word)
            if len(best) > 0: res.append_message(best)
            if len(synos) > 0: res.append_message(synos)
            return res
        else:
            raise IMException("Aucun synonyme de %s n'a été trouvé" % word)

    elif what == "antonymes":
        if len(anton) > 0:
            res = Response(anton, channel=msg.channel,
                            title="Antonymes de %s" % word)
            return res
        else:
            raise IMException("Aucun antonyme de %s n'a été trouvé" % word)

    else:
        raise IMException("WHAT?!")
