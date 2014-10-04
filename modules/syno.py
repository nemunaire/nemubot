# coding=utf-8

"""Find synonyms"""

import json
import re
from urllib.parse import quote
from urllib.request import urlopen

from hooks import hook
from tools import web

nemubotversion = 3.4

from more import Response

def help_full():
    return "!syno [LANG] <word>: give a list of synonyms for <word>."

def load(context):
    global lang_binding

    if not CONF or not CONF.hasNode("bighugelabs") or not CONF.getNode("bighugelabs").hasAttribute("key"):
        print ("You need a NigHugeLabs API key in order to have english "
               "theasorus. Add it to the module configuration file:\n<bighugelabs"
               " key=\"XXXXXXXXXXXXXXXX\" />\nRegister at "
               "https://words.bighugelabs.com/getkey.php")
    else:
        lang_binding["en"] = lambda word: get_english_synos(CONF.getNode("bighugelabs")["key"], word)


def get_french_synos(word):
    url = "http://www.crisco.unicaen.fr/des/synonymes/" + quote(word.encode("ISO-8859-1"))
    print_debug(url)
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
    raw = urlopen("http://words.bighugelabs.com/api/2/%s/%s/json" % (quote(key), quote(word.encode("ISO-8859-1"))))
    cnt = json.loads(raw.read().decode())

    best = list(); synos = list(); anton = list()

    if cnt is not None:
        for k, c in cnt.items():
            if "syn" in c: best += c["syn"]
            if "rel" in c: synos += c["rel"]
            if "ant" in c: anton += c["ant"]

    return (best, synos, anton)


lang_binding = { 'fr': get_french_synos }


@hook("cmd_hook", "synonymes", data="synonymes")
@hook("cmd_hook", "antonymes", data="antonymes")
def go(msg, what):
    if len(msg.cmds) < 2:
        raise IRCException("de quel mot veux-tu connaître la liste des synonymes ?")

    # Detect lang
    if msg.cmds[1] in lang_binding:
        func = lang_binding[msg.cmds[1]]
        word = ' '.join(msg.cmds[2:])
    else:
        func = lang_binding["fr"]
        word = ' '.join(msg.cmds[1:])
        # TODO: depreciate usage without lang
        #raise IRCException("language %s is not handled yet." % msg.cmds[1])

    try:
        best, synos, anton = func(word)
    except:
        best, synos, anton = (list(), list(), list())

    if what == "synonymes":
        if len(synos) > 0 or len(best) > 0:
            res = Response(channel=msg.channel, title="Synonymes de %s" % word)
            if len(best) > 0: res.append_message(best)
            if len(synos) > 0: res.append_message(synos)
            return res
        else:
            raise IRCException("Aucun synonyme de %s n'a été trouvé" % word)

    elif what == "antonymes":
        if len(anton) > 0:
            res = Response(anton, channel=msg.channel,
                            title="Antonymes de %s" % word)
            return res
        else:
            raise IRCException("Aucun antonyme de %s n'a été trouvé" % word)

    else:
        raise IRCException("WHAT?!")
