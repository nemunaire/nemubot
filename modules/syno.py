# coding=utf-8

import re
import traceback
import sys
from urllib.parse import quote

from tools import web

nemubotversion = 3.3

def help_tiny ():
  return "Find french synonyms"

def help_full ():
  return "!syno <word>: give a list of synonyms for <word>."

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_syno, "synonymes"))
    add_hook("cmd_hook", Hook(cmd_anto, "antonymes"))

def cmd_syno(msg):
    return go("synonymes", msg)

def cmd_anto(msg):
    return go("antonymes", msg)

def go(what, msg):
    if len(msg.cmds) < 2:
        raise IRCException("de quel mot veux-tu connaître la liste des synonymes ?")

    word = ' '.join(msg.cmds[1:])
    try:
        best, synos, anton = get_synos(word)
    except:
        best, synos, anton = (list(), list(), list())

    if what == "synonymes":
        if len(synos) > 0:
            res = Response(msg.sender, best, channel=msg.channel,
                            title="Synonymes de %s" % word)
            res.append_message(synos)
            return res
        else:
            raise IRCException("Aucun synonyme de %s n'a été trouvé" % word)

    elif what == "antonymes":
        if len(anton) > 0:
            res = Response(msg.sender, anton, channel=msg.channel,
                            title="Antonymes de %s" % word)
            return res
        else:
            raise IRCException("Aucun antonyme de %s n'a été trouvé" % word)

    else:
        raise IRCException("WHAT?!")


def get_synos(word):
    url = "http://www.crisco.unicaen.fr/des/synonymes/" + quote(word.encode("ISO-8859-1"))
    print_debug (url)
    page = web.getURLContent(url)

    if page is not None:
        best = list()
        synos = list()
        anton = list()
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

    else:
        return (list(), list(), list())
