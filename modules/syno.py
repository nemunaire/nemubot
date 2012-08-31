# coding=utf-8

import http.client
import re
import socket
from urllib.parse import quote

nemubotversion = 3.2

def help_tiny ():
  return "Find french synonyms"

def help_full ():
  return "!syno <word> [<word> ...]: give a list of synonyms for each <word> (maximum 5 each time)."

def load(context):
    from hooks import Hook
    context.hooks.add_hook("cmd_hook", Hook(cmd_syno, "syno"))
    context.hooks.add_hook("cmd_hook", Hook(cmd_syno, "synonyme"))


def cmd_syno(msg):
    if 1 < len(msg.cmd) < 6:
        for word in msg.cmd[1:]:
            synos = get_synos(word)
            if synos is None:
                return Response(msg.sender,
                                "Une erreur s'est produite durant la recherche"
                                " d'un synonyme de %s" % word, msg.channel)
            elif len(synos) > 0:
                return Response(msg.sender,
                                "Synonymes de %s : %s" %
                                (word, ', '.join(synos)),
                                msg.channel)
            else:
                return Response(msg.sender,
                                "Aucun synonymes de %s n'a été trouvé" % word,
                                msg.channel)
    return False


def get_synos(word):
    (res, page) = getPage(word)
    if res == http.client.OK:
        synos = list()
        for line in page.decode().split("\n"):
            if re.match("[ \t]*<tr[^>]*>.*</tr>[ \t]*</table>.*", line) is not None:
                for elt in re.finditer(">&[^;]+;([^&]*)&[^;]+;<", line):
                    synos.append(elt.group(1))
        return synos
    else:
        return None


def getPage(terms):
  conn = http.client.HTTPConnection("www.crisco.unicaen.fr", timeout=5)
  try:
    conn.request("GET", "/des/synonymes/%s" % quote(terms))
  except socket.gaierror:
    print ("impossible de récupérer la page Wolfram|Alpha.")
    return (http.client.INTERNAL_SERVER_ERROR, None)

  res = conn.getresponse()
  data = res.read()

  conn.close()
  return (res.status, data)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 0:
        print ("Usage: ./syno.py word [word ...]")
    else:
        for word in sys.argv:
            synos = get_synos(word)
            if synos is not None:
                print ("Synonyme de %s : %s" % (word, ', '.join(synos)))
