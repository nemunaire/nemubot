# coding=utf-8

import re
import traceback
import sys
from urllib.parse import quote

from tools import web
from tools.web import striphtml
from collections import defaultdict

nemubotversion = 3.3

s = [('present', '0'), ('présent', '0'), ('pr', '0'),
     ('passé simple', '12'), ('passe simple', '12'), ('ps', '12'),
     ('passé antérieur', '112'), ('passe anterieur', '112'), ('pa', '112'),
     ('passé composé', '100'), ('passe compose', '100'), ('pc', '100'),
     ('futur', '18'), ('f', '18'),
     ('futur antérieur', '118'), ('futur anterieur', '118'), ('fa', '118'),
     ('subjonctif présent', '24'), ('subjonctif present', '24'), ('spr', '24'),
     ('subjonctif passé', '124'), ('subjonctif passe', '124'), ('spa', '124'),
     ('plus que parfait', '106'), ('pqp', '106'),
     ('imparfait', '6'), ('ii', '6')]

d = defaultdict(list)

for k, v in s:
  d[k].append(v)

def help_tiny ():
  return "Find french conjugaison"

def help_full ():
  return "!conjugaison <tens> <verb>: give the conjugaison for <verb> in <tens>."

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_conjug, "conjugaison"))


def cmd_conjug(msg):
    if len(msg.cmds) < 3:
      return Response(msg.sender,
                      "Demande incorrecte.\n %s" % help_full(),
                      msg.channel)

    tens = msg.cmds[1]

    for i in range(2, len(msg.cmds) - 1):
      tens += " " + msg.cmds[i]

    print_debug(tens)

    verb = msg.cmds[len(msg.cmds) - 1]

    try:
         conjug = get_conjug(verb, tens)
    except:
         conjug = None
         exc_type, exc_value, exc_traceback = sys.exc_info()
         traceback.print_exception(exc_type, exc_value,
                                   exc_traceback)

    if conjug is None:
          return Response(msg.sender,
                          "Une erreur s'est produite durant la recherche"
                          " du verbe %s" % verb, msg.channel)
    elif len(conjug) > 0:
          return Response(msg.sender, conjug, msg.channel,
                          title="Conjugaison de %s" % verb)
    else:
          return Response(msg.sender,
                          "Aucune conjugaison de %s n'a été trouvé" % verb,
                          msg.channel)
    return False


def get_conjug(verb, stringTens):
    url = "http://leconjugueur.lefigaro.fr/conjugaison/verbe/" + quote(verb.encode("ISO-8859-1")) + ".html"
    print_debug (url)
    page = web.getURLContent(url)
    if page is not None:
        for line in page.split("\n"):
            if re.search('<div class="modeBloc">', line) is not None:
              return compute_line(line, stringTens)
    else:
        return None

def compute_line(line, stringTens):
  res = list()
  try:
    idTemps = d[stringTens]
  except:
    res.append("Le temps demandé n'existe pas")
    return res

  if len(idTemps) == 0:
    res.append("Le temps demandé n'existe pas")
    return res

  index = line.index('<div id="temps' + idTemps[0] + '\"')
  endIndex = line[index:].index('<div class=\"conjugBloc\"')

  endIndex += index
  newLine = line[index:endIndex]

  for elt in re.finditer("[p|/]>([^/]*/b>)", newLine):
    res.append(striphtml(elt.group(1)))

  return res

