# coding=utf-8

"""Create countdowns and reminders"""

import re
from datetime import datetime, timedelta, timezone

from nemubot import context
from nemubot.exception import IMException
from nemubot.event import ModuleEvent
from nemubot.hooks import hook
from nemubot.tools.countdown import countdown_format, countdown
from nemubot.tools.date import extractDate
from nemubot.tools.xmlparser.node import ModuleState

nemubotversion = 3.4

from more import Response

def help_full ():
    return "This module store a lot of events: ny, we, " + (", ".join(context.datas.index.keys())) + "\n!eventslist: gets list of timer\n!start /something/: launch a timer"

def load(context):
    #Define the index
    context.data.setIndex("name")

    for evt in context.data.index.keys():
        if context.data.index[evt].hasAttribute("end"):
            event = ModuleEvent(call=fini, call_data=dict(strend=context.data.index[evt]))
            event._end = context.data.index[evt].getDate("end")
            idt = context.add_event(event)
            if idt is not None:
                context.data.index[evt]["_id"] = idt


def fini(d, strend):
    context.send_response(strend["server"], Response("%s arrivé à échéance." % strend["name"], channel=strend["channel"], nick=strend["proprio"]))
    context.data.delChild(context.data.index[strend["name"]])
    context.save()

@hook.command("goûter")
def cmd_gouter(msg):
    ndate = datetime.now(timezone.utc)
    ndate = datetime(ndate.year, ndate.month, ndate.day, 16, 42, 0, 0, timezone.utc)
    return Response(countdown_format(ndate,
                             "Le goûter aura lieu dans %s, préparez vos biscuits !",
                             "Nous avons %s de retard pour le goûter :("),
                    channel=msg.channel)

@hook.command("week-end")
def cmd_we(msg):
    ndate = datetime.now(timezone.utc) + timedelta(5 - datetime.today().weekday())
    ndate = datetime(ndate.year, ndate.month, ndate.day, 0, 0, 1, 0, timezone.utc)
    return Response(countdown_format(ndate,
                             "Il reste %s avant le week-end, courage ;)",
                             "Youhou, on est en week-end depuis %s."),
                    channel=msg.channel)

@hook.command("start")
def start_countdown(msg):
    """!start /something/: launch a timer"""
    if len(msg.args) < 1:
        raise IMException("indique le nom d'un événement à chronométrer")
    if msg.args[0] in context.data.index:
        raise IMException("%s existe déjà." % msg.args[0])

    strnd = ModuleState("strend")
    strnd["server"] = msg.server
    strnd["channel"] = msg.channel
    strnd["proprio"] = msg.nick
    strnd["start"] = msg.date
    strnd["name"] = msg.args[0]
    context.data.addChild(strnd)

    evt = ModuleEvent(call=fini, call_data=dict(strend=strnd))

    if len(msg.args) > 1:
        result1 = re.findall("([0-9]+)([smhdjwyaSMHDJWYA])?", msg.args[1])
        result2 = re.match("(.*[^0-9])?([0-3]?[0-9])/([0-1]?[0-9])/((19|20)?[01239][0-9])", msg.args[1])
        result3 = re.match("(.*[^0-9])?([0-2]?[0-9]):([0-5]?[0-9])(:([0-5]?[0-9]))?", msg.args[1])
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
                strnd["_id"] = context.add_event(evt)
            except:
                context.data.delChild(strnd)
                raise IMException("Mauvais format de date pour l'événement %s. Il n'a pas été créé." % msg.args[0])

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
            eid = context.add_event(evt)
            if eid is not None:
                strnd["_id"] = eid

    context.save()
    if "end" in strnd:
        return Response("%s commencé le %s et se terminera le %s." %
                        (msg.args[0], msg.date.strftime("%A %d %B %Y à %H:%M:%S"),
                         strnd.getDate("end").strftime("%A %d %B %Y à %H:%M:%S")),
                        nick=msg.frm)
    else:
        return Response("%s commencé le %s"% (msg.args[0],
                            msg.date.strftime("%A %d %B %Y à %H:%M:%S")),
                        nick=msg.frm)

@hook.command("end")
@hook.command("forceend")
def end_countdown(msg):
    if len(msg.args) < 1:
        raise IMException("quel événement terminer ?")

    if msg.args[0] in context.data.index:
        if context.data.index[msg.args[0]]["proprio"] == msg.nick or (msg.cmd == "forceend" and msg.frm_owner):
            duration = countdown(msg.date - context.data.index[msg.args[0]].getDate("start"))
            context.del_event(context.data.index[msg.args[0]]["_id"])
            context.data.delChild(context.data.index[msg.args[0]])
            context.save()
            return Response("%s a duré %s." % (msg.args[0], duration),
                            channel=msg.channel, nick=msg.nick)
        else:
            raise IMException("Vous ne pouvez pas terminer le compteur %s, créé par %s." % (msg.args[0], context.data.index[msg.args[0]]["proprio"]))
    else:
        return Response("%s n'est pas un compteur connu."% (msg.args[0]), channel=msg.channel, nick=msg.nick)

@hook.command("eventslist")
def liste(msg):
    """!eventslist: gets list of timer"""
    if len(msg.args):
        res = list()
        for user in msg.args:
            cmptr = [x["name"] for x in context.data.index.values() if x["proprio"] == user]
            if len(cmptr) > 0:
                res.append("Compteurs créés par %s : %s" % (user, ", ".join(cmptr)))
            else:
                res.append("%s n'a pas créé de compteur" % user)
        return Response(" ; ".join(res), channel=msg.channel)
    else:
        return Response("Compteurs connus : %s." % ", ".join(context.data.index.keys()), channel=msg.channel)

@hook.command()
def parseanswer(msg):
    if msg.cmd in context.data.index:
        res = Response(channel=msg.channel)

        # Avoid message starting by ! which can be interpreted as command by other bots
        if msg.cmd[0] == "!":
            res.nick = msg.nick

        if context.data.index[msg.cmd].name == "strend":
            if context.data.index[msg.cmd].hasAttribute("end"):
                res.append_message("%s commencé il y a %s et se terminera dans %s." % (msg.cmd, countdown(msg.date - context.data.index[msg.cmd].getDate("start")), countdown(context.data.index[msg.cmd].getDate("end") - msg.date)))
            else:
                res.append_message("%s commencé il y a %s." % (msg.cmd, countdown(msg.date - context.data.index[msg.cmd].getDate("start"))))
        else:
            res.append_message(countdown_format(context.data.index[msg.cmd].getDate("start"), context.data.index[msg.cmd]["msg_before"], context.data.index[msg.cmd]["msg_after"]))
        return res

RGXP_ask = re.compile(r"^.*((create|new)\s+(a|an|a\s*new|an\s*other)?\s*(events?|commande?)|(nouvel(le)?|ajoute|cr[ée]{1,3})\s+(un)?\s*([eé]v[ée]nements?|commande?)).*$", re.I)

@hook.ask()
def parseask(msg):
    if RGXP_ask.match(msg.text) is not None:
        name = re.match("^.*!([^ \"'@!]+).*$", msg.text)
        if name is None:
            raise IMException("il faut que tu attribues une commande à l'événement.")
        if name.group(1) in context.data.index:
            raise IMException("un événement portant ce nom existe déjà.")

        texts = re.match("^[^\"]*(avant|après|apres|before|after)?[^\"]*\"([^\"]+)\"[^\"]*((avant|après|apres|before|after)?.*\"([^\"]+)\".*)?$", msg.text, re.I)
        if texts is not None and texts.group(3) is not None:
            extDate = extractDate(msg.text)
            if extDate is None or extDate == "":
                raise IMException("la date de l'événement est invalide !")

            if texts.group(1) is not None and (texts.group(1) == "après" or texts.group(1) == "apres" or texts.group(1) == "after"):
                msg_after = texts.group (2)
                msg_before = texts.group (5)
            if (texts.group(4) is not None and (texts.group(4) == "après" or texts.group(4) == "apres" or texts.group(4) == "after")) or texts.group(1) is None:
                msg_before = texts.group (2)
                msg_after = texts.group (5)

            if msg_before.find("%s") == -1 or msg_after.find("%s") == -1:
                raise IMException("Pour que l'événement soit valide, ajouter %s à"
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
            context.data.addChild(evt)
            context.save()
            return Response("Nouvel événement !%s ajouté avec succès." % name.group(1),
                            channel=msg.channel)

        elif texts is not None and texts.group (2) is not None:
            evt = ModuleState("event")
            evt["server"] = msg.server
            evt["channel"] = msg.channel
            evt["proprio"] = msg.nick
            evt["name"] = name.group(1)
            evt["msg_before"] = texts.group (2)
            context.data.addChild(evt)
            context.save()
            return Response("Nouvelle commande !%s ajoutée avec succès." % name.group(1),
                            channel=msg.channel)

        else:
            raise IMException("Veuillez indiquez les messages d'attente et d'après événement entre guillemets.")
