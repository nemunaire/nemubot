# coding=utf-8

import re
import traceback
import sys
from urllib.parse import quote

from tools import web
from tools.web import striphtml

nemubotversion = 3.3

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
    verb = msg.cmds[2]
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
  idTemps = get_conjug_for_tens(stringTens)

  if idTemps is None:
     return Response(msg.sender,
                     "Le temps que vous avez spécifiez n'existe pas", msg.channel)

  index = line.index('<div id="temps' + idTemps + '\"')
  endIndex = line[index:].index('<div class=\"conjugBloc\"')

  endIndex += index
  newLine = line[index:endIndex]

  for elt in re.finditer("[p|/]>([^/]*/b>)", newLine):
#    res.append(strip_tags(elt.group(1)))
    res.append(striphtml(elt.group(1)))

  return res
  

def get_conjug_for_tens(stringTens):
  dic = {'pr' : '0',
         'ps' : '12',
         'pa' : '112',
         'pc' : '100',
         'f'  : '18',
         'fa' : '118',
         'spr' : '24',
         'spa' : '124',
         'ii' : '6',
         'pqp' : '106'}

  return dic[stringTens]

