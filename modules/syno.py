# coding=utf-8

import http.client
import re
import socket
from urllib.parse import quote

nemubotversion = 3.0

import module_states_file as xmlparser

def help_tiny ():
  return "Find french synonyms"

def help_full ():
  return "!syno <word> [<word> ...]: give a list of synonyms for each <word> (maximum 5 each time)."


def parseanswer(msg):
  if msg.cmd[0] == "syno" or msg.cmd[0] == "synonyme":
    if 1 < len(msg.cmd) < 6:
      for syno in msg.cmd[1:]:
        (res, page) = getPage(syno)
        if res == http.client.OK:
          synos = list()
          for line in page.decode().split("\n"):
            if re.match("[ \t]*<tr[^>]*>.*</tr>[ \t]*</table>.*", line) is not None:
              for elt in re.finditer("&#160([^&]*)&#160", line):
                synos.append(elt.group(1))
          if len(synos) > 0:
            msg.send_chn("Synonymes de %s : %s" % (syno, ', '.join(synos)))
          else:
            msg.send_chn("Aucun synonymes de %s n'a été trouvé"%syno)
        else:
          msg.send_chn("Une erreur s'est produite durant la recherche d'un synonyme de %s" % syno)
    return True
  return False


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
