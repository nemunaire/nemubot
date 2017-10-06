"""Find french conjugaison"""

# PYTHON STUFFS #######################################################

from collections import defaultdict
import re
from urllib.parse import quote

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web
from nemubot.tools.web import striphtml

from nemubot.module.more import Response


# GLOBALS #############################################################

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


# MODULE CORE #########################################################

def get_conjug(verb, stringTens):
    url = ("https://leconjugueur.lefigaro.fr/conjugaison/verbe/%s.html" %
           quote(verb.encode("ISO-8859-1")))
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
        raise IMException("le temps demandé n'existe pas")

    if len(idTemps) == 0:
        raise IMException("le temps demandé n'existe pas")

    index = line.index('<div id="temps' + idTemps[0] + '\"')
    endIndex = line[index:].index('<div class=\"conjugBloc\"')

    endIndex += index
    newLine = line[index:endIndex]

    res = list()
    for elt in re.finditer("[p|/]>([^/]*/b>)", newLine):
        res.append(striphtml(elt.group(1)
                             .replace("<b>", "\x02")
                             .replace("</b>", "\x0F")))
    return res


# MODULE INTERFACE ####################################################

@hook.command("conjugaison",
      help_usage={
          "TENS VERB": "give the conjugaison for VERB in TENS."
      })
def cmd_conjug(msg):
    if len(msg.args) < 2:
        raise IMException("donne moi un temps et un verbe, et je te donnerai "
                           "sa conjugaison!")

    tens = ' '.join(msg.args[:-1])

    verb = msg.args[-1]

    conjug = get_conjug(verb, tens)

    if len(conjug) > 0:
        return Response(conjug, channel=msg.channel,
                        title="Conjugaison de %s" % verb)
    else:
        raise IMException("aucune conjugaison de '%s' n'a été trouvé" % verb)
