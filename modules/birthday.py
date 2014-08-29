# coding=utf-8

"""People birthdays and ages"""

import re
import sys
from datetime import datetime
from datetime import date

from hooks import hook
from tools.countdown import countdown_format
from xmlparser.node import ModuleState

nemubotversion = 3.4

def load(context):
    global DATAS
    DATAS.setIndex("name", "birthday")


def help_full():
    return "!anniv /who/: gives the remaining time before the anniversary of /who/\n!age /who/: gives the age of /who/\nIf /who/ is not given, gives the remaining time before your anniversary.\n\n To set yout birthday, say it to nemubot :)"


def findName(msg):
    if len(msg.cmds) < 2 or msg.cmds[1].lower() == "moi" or msg.cmds[1].lower() == "me":
        name = msg.nick.lower()
    else:
        name = msg.cmds[1].lower()

    matches = []

    if name in DATAS.index:
        matches.append(name)
    else:
        for k in DATAS.index.keys ():
            if k.find (name) == 0:
                matches.append (k)
    return (matches, name)


@hook("cmd_hook", "anniv")
def cmd_anniv(msg):
    (matches, name) = findName(msg)
    if len(matches) == 1:
        name = matches[0]
        tyd = DATAS.index[name].getDate("born")
        tyd = datetime(date.today().year, tyd.month, tyd.day)

        if (tyd.day == datetime.today().day and
            tyd.month == datetime.today().month):
            return Response(msg.sender, countdown_format(
                    DATAS.index[name].getDate("born"), "",
                    "C'est aujourd'hui l'anniversaire de %s !"
                    " Il a %s. Joyeux anniversaire :)" % (name, "%s")),
                            msg.channel)
        else:
            if tyd < datetime.today():
                tyd = datetime(date.today().year + 1, tyd.month, tyd.day)

            return Response(msg.sender, countdown_format(tyd,
                            "Il reste %s avant l'anniversaire de %s !" % ("%s",
                                                                    name), ""),
                            msg.channel)
    else:
        return Response(msg.sender, "désolé, je ne connais pas la date d'anniversaire"
                        " de %s. Quand est-il né ?" % name,
                        msg.channel, msg.nick)

@hook("cmd_hook", "age")
def cmd_age(msg):
    (matches, name) = findName(msg)
    if len(matches) == 1:
        name = matches[0]
        d = DATAS.index[name].getDate("born")

        return Response(msg.sender, countdown_format(d,
                                        "%s va naître dans %s." % (name, "%s"),
                                        "%s a %s." % (name, "%s")),
                        msg.channel)
    else:
        return Response(msg.sender, "désolé, je ne connais pas l'âge de %s."
                        " Quand est-il né ?" % name, msg.channel, msg.nick)
    return True

@hook("ask_default")
def parseask(msg):
    res = re.match(r"^(\S+)\s*('s|suis|est|is|was|were)?\s+(birthday|geburtstag|née? |nee? le|born on).*$", msg.text, re.I)
    if res is not None:
        try:
            extDate = msg.extractDate()
            if extDate is None or extDate.year > datetime.now().year:
                return Response(msg.sender,
                                "la date de naissance ne paraît pas valide...",
                                msg.channel,
                                msg.nick)
            else:
                nick = res.group(1)
                if nick == "my" or nick == "I" or nick == "i" or nick == "je" or nick == "mon" or nick == "ma":
                    nick = msg.nick
                if nick.lower() in DATAS.index:
                    DATAS.index[msg.nick.lower()]["born"] = extDate
                else:
                    ms = ModuleState("birthday")
                    ms.setAttribute("name", nick.lower())
                    ms.setAttribute("born", extDate)
                    DATAS.addChild(ms)
                save()
                return Response(msg.sender,
                                "ok, c'est noté, %s est né le %s"
                                % (nick, extDate.strftime("%A %d %B %Y à %H:%M")),
                                msg.channel,
                                msg.nick)
        except:
            raise IRCException("la date de naissance ne paraît pas valide.")
