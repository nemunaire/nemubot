"""People birthdays and ages"""

# PYTHON STUFFS #######################################################

import re
import sys
from datetime import date, datetime

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools.countdown import countdown_format
from nemubot.tools.date import extractDate
from nemubot.tools.xmlparser.node import ModuleState

from more import Response


# LOADING #############################################################

def load(context):
    context.data.setIndex("name", "birthday")


# MODULE CORE #########################################################

def findName(msg):
    if (not len(msg.args) or msg.args[0].lower() == "moi" or
        msg.args[0].lower() == "me"):
        name = msg.nick.lower()
    else:
        name = msg.args[0].lower()

    matches = []

    if name in context.data.index:
        matches.append(name)
    else:
        for k in context.data.index.keys():
            if k.find(name) == 0:
                matches.append(k)
    return (matches, name)


# MODULE INTERFACE ####################################################

## Commands

@hook.command("anniv",
      help="gives the remaining time before the anniversary of known people",
      help_usage={
          None: "Calculate the time remaining before your birthday",
          "WHO": "Calculate the time remaining before WHO's birthday",
      })
def cmd_anniv(msg):
    (matches, name) = findName(msg)
    if len(matches) == 1:
        name = matches[0]
        tyd = context.data.index[name].getDate("born")
        tyd = datetime(date.today().year, tyd.month, tyd.day)

        if (tyd.day == datetime.today().day and
            tyd.month == datetime.today().month):
            return Response(countdown_format(
                context.data.index[name].getDate("born"), "",
                "C'est aujourd'hui l'anniversaire de %s !"
                " Il a %s. Joyeux anniversaire :)" % (name, "%s")),
                            msg.channel)
        else:
            if tyd < datetime.today():
                tyd = datetime(date.today().year + 1, tyd.month, tyd.day)

            return Response(countdown_format(tyd,
                            "Il reste %s avant l'anniversaire de %s !" % ("%s",
                                                                    name), ""),
                            msg.channel)
    else:
        return Response("désolé, je ne connais pas la date d'anniversaire"
                        " de %s. Quand est-il né ?" % name,
                        msg.channel, msg.nick)


@hook.command("age",
      help="Calculate age of known people",
      help_usage={
          None: "Calculate your age",
          "WHO": "Calculate the age of WHO"
      })
def cmd_age(msg):
    (matches, name) = findName(msg)
    if len(matches) == 1:
        name = matches[0]
        d = context.data.index[name].getDate("born")

        return Response(countdown_format(d,
                                         "%s va naître dans %s." % (name, "%s"),
                                         "%s a %s." % (name, "%s")),
                        msg.channel)
    else:
        return Response("désolé, je ne connais pas l'âge de %s."
                        " Quand est-il né ?" % name, msg.channel, msg.nick)
    return True


## Input parsing

@hook.ask()
def parseask(msg):
    res = re.match(r"^(\S+)\s*('s|suis|est|is|was|were)?\s+(birthday|geburtstag|née? |nee? le|born on).*$", msg.text, re.I)
    if res is not None:
        try:
            extDate = extractDate(msg.text)
            if extDate is None or extDate.year > datetime.now().year:
                return Response("la date de naissance ne paraît pas valide...",
                                msg.channel,
                                msg.nick)
            else:
                nick = res.group(1)
                if nick == "my" or nick == "I" or nick == "i" or nick == "je" or nick == "mon" or nick == "ma":
                    nick = msg.nick
                if nick.lower() in context.data.index:
                    context.data.index[nick.lower()]["born"] = extDate
                else:
                    ms = ModuleState("birthday")
                    ms.setAttribute("name", nick.lower())
                    ms.setAttribute("born", extDate)
                    context.data.addChild(ms)
                context.save()
                return Response("ok, c'est noté, %s est né le %s"
                                % (nick, extDate.strftime("%A %d %B %Y à %H:%M")),
                                msg.channel,
                                msg.nick)
        except:
            raise IMException("la date de naissance ne paraît pas valide.")
