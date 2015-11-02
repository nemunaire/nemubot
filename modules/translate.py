"""Translation module"""

# PYTHON STUFFS #######################################################

from urllib.parse import quote

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from more import Response


# GLOBALS #############################################################

LANG = ["ar", "zh", "cz", "en", "fr", "gr", "it",
        "ja", "ko", "pl", "pt", "ro", "es", "tr"]
URL = "http://api.wordreference.com/0.8/%s/json/%%s%%s/%%s"


# LOADING #############################################################

def load(context):
    if not context.config or "wrapikey" not in context.config:
        raise ImportError("You need a WordReference API key in order to use "
                          "this module. Add it to the module configuration "
                          "file:\n<module name=\"translate\" wrapikey=\"XXXXX\""
                          " />\nRegister at http://"
                          "www.wordreference.com/docs/APIregistration.aspx")
    global URL
    URL = URL % context.config["wrapikey"]


# MODULE CORE #########################################################

def meaning(entry):
    ret = list()
    if "sense" in entry and len(entry["sense"]) > 0:
        ret.append('« %s »' % entry["sense"])
    if "usage" in entry and len(entry["usage"]) > 0:
        ret.append(entry["usage"])
    if len(ret) > 0:
        return " as " + "/".join(ret)
    else:
        return ""


def extract_traslation(entry):
    ret = list()
    for i in [ "FirstTranslation", "SecondTranslation", "ThirdTranslation", "FourthTranslation" ]:
        if i in entry:
            ret.append("\x03\x02%s\x03\x02%s" % (entry[i]["term"], meaning(entry[i])))
    if "Note" in entry and entry["Note"]:
        ret.append("note: %s" % entry["Note"])
    return ", ".join(ret)


def translate(term, langFrom="en", langTo="fr"):
    wres = web.getJSON(URL % (langFrom, langTo, quote(term)))

    if "Error" in wres:
        raise IMException(wres["Note"])

    else:
        for k in sorted(wres.keys()):
            t = wres[k]
            if len(k) > 4 and k[:4] == "term":
                if "Entries" in t:
                    ent = t["Entries"]
                else:
                    ent = t["PrincipalTranslations"]

                for i in sorted(ent.keys()):
                    yield "Translation of %s%s: %s" % (
                            ent[i]["OriginalTerm"]["term"],
                            meaning(ent[i]["OriginalTerm"]),
                            extract_traslation(ent[i]))


# MODULE INTERFACE ####################################################

@hook.command("translate",
      help="Word translation using WordReference.com",
      help_usage={
          "TERM": "Found translation of TERM from/to english to/from <lang>."
      },
      keywords={
          "from=LANG": "language of the term you asked for translation between: en, " + ", ".join(LANG),
          "to=LANG": "language of the translated terms between: en, " + ", ".join(LANG),
      })
def cmd_translate(msg):
    if not len(msg.args):
        raise IMException("which word would you translate?")

    langFrom = msg.kwargs["from"] if "from" in msg.kwargs else "en"
    if "to" in msg.kwargs:
        langTo = msg.kwargs["to"]
    else:
        langTo = "fr" if langFrom == "en" else "en"

    if langFrom not in LANG or langTo not in LANG:
        raise IMException("sorry, I can only translate to or from: " + ", ".join(LANG))
    if langFrom != "en" and langTo != "en":
        raise IMException("sorry, I can only translate to or from english")

    res = Response(channel=msg.channel,
                   count=" (%d more meanings)",
                   nomore="No more translation")
    for t in translate(" ".join(msg.args), langFrom=langFrom, langTo=langTo):
        res.append_message(t)
    return res
