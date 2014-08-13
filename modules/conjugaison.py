# coding=utf-8

import re
import traceback
import sys
from urllib.parse import quote

from hooks import hook
from tools import web
from tools.web import striphtml
from collections import defaultdict

nemubotversion = 3.4

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

def help_tiny():
  return "Find french conjugaison"

def help_full():
  return "!conjugaison <tens> <verb>: give the conjugaison for <verb> in <tens>."


@hook("cmd_hook", "conjugaison", help="!conjugaison <tens> <verb>: give the conjugaison for <verb> in <tens>.")
def cmd_conjug(msg):
    if len(msg.cmds) < 3:
        raise IRCException("donne moi un temps et un verbe, et je te donnerai sa conjugaison!")

    tens = ' '.join(msg.cmds[1:-1])
    print_debug(tens)

    verb = msg.cmds[-1]

    conjug = get_conjug(verb, tens)

    if len(conjug) > 0:
        return Response(msg.sender, conjug, channel=msg.channel,
                        title="Conjugaison de %s" % verb)
    else:
        raise IRCException("aucune conjugaison de '%s' n'a été trouvé" % verb)


def get_conjug(verb, stringTens):
    url = ("http://leconjugueur.lefigaro.fr/conjugaison/verbe/%s.html" %
           quote(verb.encode("ISO-8859-1")))
    print_debug (url)
    page = web.getURLContent(url)

    if page is not None:
        for line in page.split("\n"):
            if re.search('<div class="modeBloc">', line) is not None:
              return compute_line(line, stringTens)
    return list()

def compute_line(line, stringTens):
  try:
      idTemps = d[stringTens]
  except:
      raise IRCException("le temps demandé n'existe pas")

  if len(idTemps) == 0:
      raise IRCException("le temps demandé n'existe pas")

  index = line.index('<div id="temps' + idTemps[0] + '\"')
  endIndex = line[index:].index('<div class=\"conjugBloc\"')

  endIndex += index
  newLine = line[index:endIndex]

  res = list()
  for elt in re.finditer("[p|/]>([^/]*/b>)", newLine):
      res.append(striphtml(elt.group(1).replace("<b>", "\x02").replace("</b>", "\x0F")))
  return res
