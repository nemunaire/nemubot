"""Create countdowns and reminders"""

import calendar
from datetime import datetime, timedelta, timezone
from functools import partial
import re

from nemubot import context
from nemubot.exception import IMException
from nemubot.event import ModuleEvent
from nemubot.hooks import hook
from nemubot.message import Command
from nemubot.tools.countdown import countdown_format, countdown
from nemubot.tools.date import extractDate
from nemubot.tools.xmlparser.basic import DictNode

from nemubot.module.more import Response


class Event:

    def __init__(self, server, channel, creator, start_time, end_time=None):
        self._server = server
        self._channel = channel
        self._creator = creator
        self._start = datetime.utcfromtimestamp(float(start_time)).replace(tzinfo=timezone.utc) if not isinstance(start_time, datetime) else start_time
        self._end = datetime.utcfromtimestamp(float(end_time)).replace(tzinfo=timezone.utc) if end_time else None
        self._evt = None


    def __del__(self):
        if self._evt is not None:
            context.del_event(self._evt)
            self._evt = None


    def saveElement(self, store, tag="event"):
        attrs = {
            "server": str(self._server),
            "channel": str(self._channel),
            "creator": str(self._creator),
            "start_time": str(calendar.timegm(self._start.timetuple())),
        }
        if self._end:
            attrs["end_time"] = str(calendar.timegm(self._end.timetuple()))
        store.startElement(tag, attrs)
        store.endElement(tag)

    @property
    def creator(self):
        return self._creator

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, c):
        self._end = c

    @end.deleter
    def end(self):
        self._end = None


def help_full ():
    return "This module store a lot of events: ny, we, " + (", ".join(context.datas.keys()) if hasattr(context, "datas") else "") + "\n!eventslist: gets list of timer\n!start /something/: launch a timer"


def load(context):
    context.set_knodes({
        "dict": DictNode,
        "event": Event,
    })

    if context.data is None:
        context.set_default(DictNode())

    # Relaunch all timers
    for kevt in context.data:
        if context.data[kevt].end:
            context.data[kevt]._evt = context.add_event(ModuleEvent(partial(fini, kevt, context.data[kevt]), offset=context.data[kevt].end - datetime.now(timezone.utc), interval=0))


def fini(name, evt):
    context.send_response(evt._server, Response("%s arrivé à échéance." % name, channel=evt._channel, nick=evt.creator))
    evt._evt = None
    del context.data[name]
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
    if msg.args[0] in context.data:
        raise IMException("%s existe déjà." % msg.args[0])

    evt = Event(server=msg.server, channel=msg.channel, creator=msg.frm, start_time=msg.date)

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
                    evt.end = datetime(yea, int(result2.group(3)), int(result2.group(2)), hou, minu, sec, timezone.utc)
                elif result2 is not None:
                    evt.end = datetime(int(result2.group(4)), int(result2.group(3)), int(result2.group(2)), 0, 0, 0, timezone.utc)
                elif result3 is not None:
                  if hou * 3600 + minu * 60 + sec > now.hour * 3600 + now.minute * 60 + now.second:
                    evt.end = datetime(now.year, now.month, now.day, hou, minu, sec, timezone.utc)
                  else:
                    evt.end = datetime(now.year, now.month, now.day + 1, hou, minu, sec, timezone.utc)
            except:
                raise IMException("Mauvais format de date pour l'événement %s. Il n'a pas été créé." % msg.args[0])

        elif result1 is not None and len(result1) > 0:
            evt.end = msg.date
            for (t, g) in result1:
                if g is None or g == "" or g == "m" or g == "M":
                    evt.end += timedelta(minutes=int(t))
                elif g == "h" or g == "H":
                    evt.end += timedelta(hours=int(t))
                elif g == "d" or g == "D" or g == "j" or g == "J":
                    evt.end += timedelta(days=int(t))
                elif g == "w" or g == "W":
                    evt.end += timedelta(days=int(t)*7)
                elif g == "y" or g == "Y" or g == "a" or g == "A":
                    evt.end += timedelta(days=int(t)*365)
                else:
                    evt.end += timedelta(seconds=int(t))

    context.data[msg.args[0]] = evt
    context.save()

    if evt.end is not None:
        context.add_event(ModuleEvent(partial(fini, msg.args[0], evt),
                                      offset=evt.end - datetime.now(timezone.utc),
                                      interval=0))
        return Response("%s commencé le %s et se terminera le %s." %
                        (msg.args[0], msg.date.strftime("%A %d %B %Y à %H:%M:%S"),
                         evt.end.strftime("%A %d %B %Y à %H:%M:%S")),
                        channel=msg.channel)
    else:
        return Response("%s commencé le %s"% (msg.args[0],
                            msg.date.strftime("%A %d %B %Y à %H:%M:%S")),
                        channel=msg.channel)


@hook.command("end")
@hook.command("forceend")
def end_countdown(msg):
    if len(msg.args) < 1:
        raise IMException("quel événement terminer ?")

    if msg.args[0] in context.data:
        if context.data[msg.args[0]].creator == msg.frm or (msg.cmd == "forceend" and msg.frm_owner):
            duration = countdown(msg.date - context.data[msg.args[0]].start)
            del context.data[msg.args[0]]
            context.save()
            return Response("%s a duré %s." % (msg.args[0], duration),
                            channel=msg.channel, nick=msg.frm)
        else:
            raise IMException("Vous ne pouvez pas terminer le compteur %s, créé par %s." % (msg.args[0], context.data[msg.args[0]].creator))
    else:
        return Response("%s n'est pas un compteur connu."% (msg.args[0]), channel=msg.channel, nick=msg.frm)


@hook.command("eventslist")
def liste(msg):
    """!eventslist: gets list of timer"""
    if len(msg.args):
        res = Response(channel=msg.channel)
        for user in msg.args:
            cmptr = [k for k in context.data if context.data[k].creator == user]
            if len(cmptr) > 0:
                res.append_message(cmptr, title="Events created by %s" % user)
            else:
                res.append_message("%s doesn't have any counting events" % user)
        return res
    else:
        return Response(list(context.data.keys()), channel=msg.channel, title="Known events")


@hook.command(match=lambda msg: isinstance(msg, Command) and msg.cmd in context.data)
def parseanswer(msg):
    res = Response(channel=msg.channel)

    # Avoid message starting by ! which can be interpreted as command by other bots
    if msg.cmd[0] == "!":
        res.nick = msg.frm

    if msg.cmd in context.data:
        if context.data[msg.cmd].end:
            res.append_message("%s commencé il y a %s et se terminera dans %s." % (msg.cmd, countdown(msg.date - context.data[msg.cmd].start), countdown(context.data[msg.cmd].end - msg.date)))
        else:
            res.append_message("%s commencé il y a %s." % (msg.cmd, countdown(msg.date - context.data[msg.cmd].start)))
    else:
        res.append_message(countdown_format(context.data[msg.cmd].start, context.data[msg.cmd]["msg_before"], context.data[msg.cmd]["msg_after"]))
    return res


RGXP_ask = re.compile(r"^.*((create|new)\s+(a|an|a\s*new|an\s*other)?\s*(events?|commande?)|(nouvel(le)?|ajoute|cr[ée]{1,3})\s+(un)?\s*([eé]v[ée]nements?|commande?)).*$", re.I)

@hook.ask(match=lambda msg: RGXP_ask.match(msg.message))
def parseask(msg):
    name = re.match("^.*!([^ \"'@!]+).*$", msg.message)
    if name is None:
        raise IMException("il faut que tu attribues une commande à l'événement.")
    if name.group(1) in context.data:
        raise IMException("un événement portant ce nom existe déjà.")

    texts = re.match("^[^\"]*(avant|après|apres|before|after)?[^\"]*\"([^\"]+)\"[^\"]*((avant|après|apres|before|after)?.*\"([^\"]+)\".*)?$", msg.message, re.I)
    if texts is not None and texts.group(3) is not None:
        extDate = extractDate(msg.message)
        if extDate is None or extDate == "":
            raise IMException("la date de l'événement est invalide !")

        if texts.group(1) is not None and (texts.group(1) == "après" or texts.group(1) == "apres" or texts.group(1) == "after"):
            msg_after = texts.group(2)
            msg_before = texts.group(5)
        if (texts.group(4) is not None and (texts.group(4) == "après" or texts.group(4) == "apres" or texts.group(4) == "after")) or texts.group(1) is None:
            msg_before = texts.group(2)
            msg_after = texts.group(5)

        if msg_before.find("%s") == -1 or msg_after.find("%s") == -1:
            raise IMException("Pour que l'événement soit valide, ajouter %s à"
                            " l'endroit où vous voulez que soit ajouté le"
                            " compte à rebours.")

        evt = ModuleState("event")
        evt["server"] = msg.server
        evt["channel"] = msg.channel
        evt["proprio"] = msg.frm
        evt["name"] = name.group(1)
        evt["start"] = extDate
        evt["msg_after"] = msg_after
        evt["msg_before"] = msg_before
        context.data.addChild(evt)
        context.save()
        return Response("Nouvel événement !%s ajouté avec succès." % name.group(1),
                        channel=msg.channel)

    elif texts is not None and texts.group(2) is not None:
        evt = ModuleState("event")
        evt["server"] = msg.server
        evt["channel"] = msg.channel
        evt["proprio"] = msg.frm
        evt["name"] = name.group(1)
        evt["msg_before"] = texts.group (2)
        context.data.addChild(evt)
        context.save()
        return Response("Nouvelle commande !%s ajoutée avec succès." % name.group(1),
                        channel=msg.channel)

    else:
        raise IMException("Veuillez indiquez les messages d'attente et d'après événement entre guillemets.")
