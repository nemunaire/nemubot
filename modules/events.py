# coding=utf-8

"""Create countdowns and reminders"""

import imp
import re
import sys
from datetime import datetime, timedelta, timezone
import time
import threading
import traceback

from nemubot.event import ModuleEvent
from nemubot.hooks import hook
from nemubot.tools.date import extractDate
from nemubot.tools.countdown import countdown_format, countdown

nemubotversion = 3.4

from more import Response

def help_full ():
    return "This module store a lot of events: ny, we, " + (", ".join(DATAS.index.keys())) + "\n!eventslist: gets list of timer\n!start /something/: launch a timer"

def load(context):
    global DATAS
    #Define the index
    DATAS.setIndex("name")

    for evt in DATAS.index.keys():
        if DATAS.index[evt].hasAttribute("end"):
            event = ModuleEvent(call=fini, call_data=dict(strend=DATAS.index[evt]))
            if DATAS.index[evt]["server"] not in context.servers:
                print("WARNING: registering event for a unexistant server: %s, please connect to it." % DATAS.index[evt]["server"])
            event._end = DATAS.index[evt].getDate("end")
            idt = add_event(event)
            if idt is not None:
                DATAS.index[evt]["_id"] = idt


def fini(d, strend):
    send_response(strend["server"], Response("%s arrivé à échéance." % strend["name"], channel=strend["channel"], nick=strend["proprio"]))
    DATAS.delChild(DATAS.index[strend["name"]])
    save()

@hook("cmd_hook", "goûter")
def cmd_gouter(msg):
    ndate = datetime.now(timezone.utc)
    ndate = datetime(ndate.year, ndate.month, ndate.day, 16, 42, 0, 0, timezone.utc)
    return Response(countdown_format(ndate,
                             "Le goûter aura lieu dans %s, préparez vos biscuits !",
                             "Nous avons %s de retard pour le goûter :("),
                    channel=msg.channel)

@hook("cmd_hook", "week-end")
def cmd_we(msg):
    ndate = datetime.now(timezone.utc) + timedelta(5 - datetime.today().weekday())
    ndate = datetime(ndate.year, ndate.month, ndate.day, 0, 0, 1, 0, timezone.utc)
    return Response(countdown_format(ndate,
                             "Il reste %s avant le week-end, courage ;)",
                             "Youhou, on est en week-end depuis %s."),
                    channel=msg.channel)

@hook("cmd_hook", "start")
def start_countdown(msg):
    """!start /something/: launch a timer"""
    if len(msg.cmds) < 2:
        raise IRCException("indique le nom d'un événement à chronométrer")
    if msg.cmds[1] in DATAS.index:
        raise IRCException("%s existe déjà." % msg.cmds[1])

    strnd = ModuleState("strend")
    strnd["server"] = msg.server
    strnd["channel"] = msg.channel
    strnd["proprio"] = msg.nick
    strnd["start"] = msg.date
    strnd["name"] = msg.cmds[1]
    DATAS.addChild(strnd)

    evt = ModuleEvent(call=fini, call_data=dict(strend=strnd))

    if len(msg.cmds) > 2:
        result1 = re.findall("([0-9]+)([smhdjwyaSMHDJWYA])?", msg.cmds[2])
        result2 = re.match("(.*[^0-9])?([0-3]?[0-9])/([0-1]?[0-9])/((19|20)?[01239][0-9])", msg.cmds[2])
        result3 = re.match("(.*[^0-9])?([0-2]?[0-9]):([0-5]?[0-9])(:([0-5]?[0-9]))?", msg.cmds[2])
        if result2 is not None or result3 is not None:
            try:
                now = msg.date
                if result3 is None or result3.group(5) is None: sec = 0
                else: sec = int(result3.group(5))
                if result3 is None or result3.group(3) is None: minu = 0
                else: minu = int(result3.group(3))
                if result3 is None or result3.group(2) is None: hou = 0
                else: hou = int(result3.group(2))
                if result2 is None or result2.group(4) is None: yea = now.year
                else: yea = int(result2.group(4))
                if result2 is not None and result3 is not None:
                    strnd["end"] = datetime(yea, int(result2.group(3)), int(result2.group(2)), hou, minu, sec, timezone.utc)
                elif result2 is not None:
                    strnd["end"] = datetime(int(result2.group(4)), int(result2.group(3)), int(result2.group(2)), 0, 0, 0, timezone.utc)
                elif result3 is not None:
                  if hou * 3600 + minu * 60 + sec > now.hour * 3600 + now.minute * 60 + now.second:
                    strnd["end"] = datetime(now.year, now.month, now.day, hou, minu, sec, timezone.utc)
                  else:
                    strnd["end"] = datetime(now.year, now.month, now.day + 1, hou, minu, sec, timezone.utc)
                evt._end = strnd.getDate("end")
                strnd["_id"] = add_event(evt)
            except:
                DATAS.delChild(strnd)
                raise IRCException("Mauvais format de date pour l'événement %s. Il n'a pas été créé." % msg.cmds[1])

        elif result1 is not None and len(result1) > 0:
            strnd["end"] = msg.date
            for (t, g) in result1:
                if g is None or g == "" or g == "m" or g == "M":
                    strnd["end"] += timedelta(minutes=int(t))
                elif g == "h" or g == "H":
                    strnd["end"] += timedelta(hours=int(t))
                elif g == "d" or g == "D" or g == "j" or g == "J":
                    strnd["end"] += timedelta(days=int(t))
                elif g == "w" or g == "W":
                    strnd["end"] += timedelta(days=int(t)*7)
                elif g == "y" or g == "Y" or g == "a" or g == "A":
                    strnd["end"] += timedelta(days=int(t)*365)
                else:
                    strnd["end"] += timedelta(seconds=int(t))
            evt._end = strnd.getDate("end")
            eid = add_event(evt)
            if eid is not None:
                strnd["_id"] = eid

    save()
    if "end" in strnd:
        return Response("%s commencé le %s et se terminera le %s." %
                        (msg.cmds[1], msg.date.strftime("%A %d %B %Y à %H:%M:%S"),
                         strnd.getDate("end").strftime("%A %d %B %Y à %H:%M:%S")),
                        nick=msg.frm)
    else:
        return Response("%s commencé le %s"% (msg.cmds[1],
                            msg.date.strftime("%A %d %B %Y à %H:%M:%S")),
                        nick=msg.frm)

@hook("cmd_hook", "end")
@hook("cmd_hook", "forceend")
def end_countdown(msg):
    if len(msg.cmds) < 2:
        raise IRCException("quel événement terminer ?")

    if msg.cmds[1] in DATAS.index:
        if DATAS.index[msg.cmds[1]]["proprio"] == msg.nick or (msg.cmds[0] == "forceend" and msg.frm_owner):
            duration = countdown(msg.date - DATAS.index[msg.cmds[1]].getDate("start"))
            del_event(DATAS.index[msg.cmds[1]]["_id"])
            DATAS.delChild(DATAS.index[msg.cmds[1]])
            save()
            return Response("%s a duré %s." % (msg.cmds[1], duration),
                            channel=msg.channel, nick=msg.nick)
        else:
            raise IRCException("Vous ne pouvez pas terminer le compteur %s, créé par %s." % (msg.cmds[1], DATAS.index[msg.cmds[1]]["proprio"]))
    else:
        return Response("%s n'est pas un compteur connu."% (msg.cmds[1]), channel=msg.channel, nick=msg.nick)

@hook("cmd_hook", "eventslist")
def liste(msg):
    """!eventslist: gets list of timer"""
    if len(msg.cmds) > 1:
        res = list()
        for user in msg.cmds[1:]:
            cmptr = [x["name"] for x in DATAS.index.values() if x["proprio"] == user]
            if len(cmptr) > 0:
                res.append("Compteurs créés par %s : %s" % (user, ", ".join(cmptr)))
            else:
                res.append("%s n'a pas créé de compteur" % user)
        return Response(" ; ".join(res), channel=msg.channel)
    else:
        return Response("Compteurs connus : %s." % ", ".join(DATAS.index.keys()), channel=msg.channel)

@hook("cmd_default")
def parseanswer(msg):
    if msg.cmds[0] in DATAS.index:
        res = Response(channel=msg.channel)

        # Avoid message starting by ! which can be interpreted as command by other bots
        if msg.cmds[0][0] == "!":
            res.nick = msg.nick

        if DATAS.index[msg.cmds[0]].name == "strend":
            if DATAS.index[msg.cmds[0]].hasAttribute("end"):
                res.append_message("%s commencé il y a %s et se terminera dans %s." % (msg.cmds[0], countdown(msg.date - DATAS.index[msg.cmds[0]].getDate("start")), countdown(DATAS.index[msg.cmds[0]].getDate("end") - msg.date)))
            else:
                res.append_message("%s commencé il y a %s." % (msg.cmds[0], countdown(msg.date - DATAS.index[msg.cmds[0]].getDate("start"))))
        else:
            res.append_message(countdown_format(DATAS.index[msg.cmds[0]].getDate("start"), DATAS.index[msg.cmds[0]]["msg_before"], DATAS.index[msg.cmds[0]]["msg_after"]))
        return res

RGXP_ask = re.compile(r"^.*((create|new)\s+(a|an|a\s*new|an\s*other)?\s*(events?|commande?)|(nouvel(le)?|ajoute|cr[ée]{1,3})\s+(un)?\s*([eé]v[ée]nements?|commande?)).*$", re.I)

@hook("ask_default")
def parseask(msg):
    if RGXP_ask.match(msg.text) is not None:
        name = re.match("^.*!([^ \"'@!]+).*$", msg.text)
        if name is None:
            raise IRCException("il faut que tu attribues une commande à l'événement.")
        if name.group(1) in DATAS.index:
            raise IRCException("un événement portant ce nom existe déjà.")

        texts = re.match("^[^\"]*(avant|après|apres|before|after)?[^\"]*\"([^\"]+)\"[^\"]*((avant|après|apres|before|after)?.*\"([^\"]+)\".*)?$", msg.text, re.I)
        if texts is not None and texts.group(3) is not None:
            extDate = extractDate(msg.text)
            if extDate is None or extDate == "":
                raise IRCException("la date de l'événement est invalide !")

            if texts.group(1) is not None and (texts.group(1) == "après" or texts.group(1) == "apres" or texts.group(1) == "after"):
                msg_after = texts.group (2)
                msg_before = texts.group (5)
            if (texts.group(4) is not None and (texts.group(4) == "après" or texts.group(4) == "apres" or texts.group(4) == "after")) or texts.group(1) is None:
                msg_before = texts.group (2)
                msg_after = texts.group (5)

            if msg_before.find("%s") == -1 or msg_after.find("%s") == -1:
                raise IRCException("Pour que l'événement soit valide, ajouter %s à"
                                " l'endroit où vous voulez que soit ajouté le"
                                " compte à rebours.")

            evt = ModuleState("event")
            evt["server"] = msg.server
            evt["channel"] = msg.channel
            evt["proprio"] = msg.nick
            evt["name"] = name.group(1)
            evt["start"] = extDate
            evt["msg_after"] = msg_after
            evt["msg_before"] = msg_before
            DATAS.addChild(evt)
            save()
            return Response("Nouvel événement !%s ajouté avec succès." % name.group(1),
                            channel=msg.channel)

        elif texts is not None and texts.group (2) is not None:
            evt = ModuleState("event")
            evt["server"] = msg.server
            evt["channel"] = msg.channel
            evt["proprio"] = msg.nick
            evt["name"] = name.group(1)
            evt["msg_before"] = texts.group (2)
            DATAS.addChild(evt)
            save()
            return Response("Nouvelle commande !%s ajoutée avec succès." % name.group(1),
                            channel=msg.channel)

        else:
            raise IRCException("Veuillez indiquez les messages d'attente et d'après événement entre guillemets.")
