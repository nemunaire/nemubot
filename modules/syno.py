# coding=utf-8

import re
from urllib.parse import quote

from tools import web

nemubotversion = 3.3

def help_tiny ():
  return "Find french synonyms"

def help_full ():
  return "!syno <word>: give a list of synonyms for <word>."

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_syno, "syno"))
    add_hook("cmd_hook", Hook(cmd_syno, "synonyme"))


def cmd_syno(msg):
    if 1 < len(msg.cmds) < 6:
        for word in msg.cmds[1:]:
            synos = get_synos(word)
            if synos is None:
                return Response(msg.sender,
                                "Une erreur s'est produite durant la recherche"
                                " d'un synonyme de %s" % word, msg.channel)
            elif len(synos) > 0:
                return Response(msg.sender, synos, msg.channel,
                                title="Synonymes de %s" % word)
            else:
                return Response(msg.sender,
                                "Aucun synonymes de %s n'a été trouvé" % word,
                                msg.channel)
    return False


def get_synos(word):
    page = web.getURLContent("http://www.crisco.unicaen.fr/des/synonymes/%s" % quote(word))
    if page is not None:
        synos = list()
        for line in page.decode().split("\n"):
            if re.match("[ \t]*<tr[^>]*>.*</tr>[ \t]*</table>.*", line) is not None:
                for elt in re.finditer(">&[^;]+;([^&]*)&[^;]+;<", line):
                    synos.append(elt.group(1))
        return synos
    else:
        return None
