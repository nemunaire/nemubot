# coding=utf-8

import imp
import re
import sys
from datetime import timedelta
from datetime import datetime
import time
import threading
import traceback

nemubotversion = 3.3

from event import ModuleEvent
from hooks import Hook

def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "events manager"

def help_full ():
    return "This module store a lot of events: ny, we, vacs, " + (", ".join(DATAS.index.keys())) + "\n!eventslist: gets list of timer\n!start /something/: launch a timer"

CONTEXT = None

def load(context):
    global DATAS, CONTEXT
    CONTEXT = context
    #Define the index
    DATAS.setIndex("name")

    for evt in DATAS.index.keys():
        if DATAS.index[evt].hasAttribute("end"):
            event = ModuleEvent(call=fini, call_data=dict(strend=DATAS.index[evt]))
            event.end = DATAS.index[evt].getDate("end")
            idt = context.add_event(event)
            if idt is not None:
                DATAS.index[evt]["id"] = idt


def fini(d, strend):
    for server in CONTEXT.servers.keys():
        if not strend.hasAttribute("server") or server == strend["server"]:
            if strend["channel"] == CONTEXT.servers[server].nick:
                CONTEXT.servers[server].send_msg_usr(strend["sender"], "%s: %s arrivé à échéance." % (strend["proprio"], strend["name"]))
            else:
                CONTEXT.servers[server].send_msg(strend["channel"], "%s: %s arrivé à échéance." % (strend["proprio"], strend["name"]))
    DATAS.delChild(DATAS.index[strend["name"]])
    save()

def cmd_gouter(msg):
    ndate = datetime.today()
    ndate = datetime(ndate.year, ndate.month, ndate.day, 16, 42)
    return Response(msg.sender,
        msg.countdown_format(ndate,
                             "Le goûter aura lieu dans %s, préparez vos biscuits !",
                             "Nous avons %s de retard pour le goûter :("),
                    channel=msg.channel)

def cmd_we(msg):
    ndate = datetime.today() + timedelta(5 - datetime.today().weekday())
    ndate = datetime(ndate.year, ndate.month, ndate.day, 0, 0, 1)
    return Response(msg.sender,
        msg.countdown_format(ndate,
                             "Il reste %s avant le week-end, courage ;)",
                             "Youhou, on est en week-end depuis %s."),
                    channel=msg.channel)

def cmd_vacances(msg):
    return Response(msg.sender,
        msg.countdown_format(datetime(2013, 7, 30, 18, 0, 1),
                             "Il reste %s avant les vacances :)",
                             "Profitons, c'est les vacances depuis %s."),
                    channel=msg.channel)

def start_countdown(msg):
    if msg.cmds[1] not in DATAS.index:

        strnd = ModuleState("strend")
        strnd["server"] = msg.server
        strnd["channel"] = msg.channel
        strnd["proprio"] = msg.nick
        strnd["sender"] = msg.sender
        strnd["start"] = datetime.now()
        strnd["name"] = msg.cmds[1]
        DATAS.addChild(strnd)

        evt = ModuleEvent(call=fini, call_data=dict(strend=strnd))

        if len(msg.cmds) > 2:
            result1 = re.findall("([0-9]+)([smhdjwyaSMHDJWYA])?", msg.cmds[2])
            result2 = re.match("(.*[^0-9])?([0-3]?[0-9])/([0-1]?[0-9])/((19|20)?[01239][0-9])", msg.cmds[2])
            result3 = re.match("(.*[^0-9])?([0-2]?[0-9]):([0-5]?[0-9])(:([0-5]?[0-9]))?", msg.cmds[2])
            if result2 is not None or result3 is not None:
                try:
                    now = datetime.now()
                    if result3 is None or result3.group(5) is None: sec = 0
                    else: sec = int(result3.group(5))
                    if result3 is None or result3.group(3) is None: minu = 0
                    else: minu = int(result3.group(3))
                    if result3 is None or result3.group(2) is None: hou = 0
                    else: hou = int(result3.group(2))

                    if result2 is None or result2.group(4) is None: yea = now.year
                    else: yea = int(result2.group(4))

                    if result2 is not None and result3 is not None:
                        strnd["end"] = datetime(yea, int(result2.group(3)), int(result2.group(2)), hou, minu, sec)
                    elif result2 is not None:
                      strnd["end"] = datetime(int(result2.group(4)), int(result2.group(3)), int(result2.group(2)))
                    elif result3 is not None:
                      if hou * 3600 + minu * 60 + sec > now.hour * 3600 + now.minute * 60 + now.second:
                        strnd["end"] = datetime(now.year, now.month, now.day, hou, minu, sec)
                      else:
                        strnd["end"] = datetime(now.year, now.month, now.day + 1, hou, minu, sec)

                    evt.end = strnd.getDate("end")
                    strnd["id"] = CONTEXT.add_event(evt)
                    save()
                    return Response(msg.sender, "%s commencé le %s et se terminera le %s." %
                                    (msg.cmds[1], datetime.now().strftime("%A %d %B %Y a %H:%M:%S"),
                                     strnd.getDate("end").strftime("%A %d %B %Y a %H:%M:%S")))
                except:
                    DATAS.delChild(strnd)
                    return Response(msg.sender,
                                    "Mauvais format de date pour l'evenement %s. Il n'a pas ete cree." % msg.cmds[1])
            elif result1 is not None and len(result1) > 0:
                strnd["end"] = datetime.now()
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
                evt.end = strnd.getDate("end")
                strnd["id"] = CONTEXT.add_event(evt)
                save()
                return Response(msg.sender, "%s commencé le %s et se terminera le %s." %
                                (msg.cmds[1], datetime.now().strftime("%A %d %B %Y a %H:%M:%S"),
                                 strnd.getDate("end").strftime("%A %d %B %Y a %H:%M:%S")))
        save()
        return Response(msg.sender, "%s commencé le %s"% (msg.cmds[1],
                            datetime.now().strftime("%A %d %B %Y a %H:%M:%S")))
    else:
        return Response(msg.sender, "%s existe déjà."% (msg.cmds[1]))

def end_countdown(msg):
    if msg.cmds[1] in DATAS.index:
        res = Response(msg.sender,
                       "%s a duré %s." % (msg.cmds[1],
                                          msg.just_countdown(datetime.now () - DATAS.index[msg.cmds[1]].getDate("start"))),
                       channel=msg.channel)
        if DATAS.index[msg.cmds[1]]["proprio"] == msg.nick or (msg.cmds[0] == "forceend" and msg.is_owner):
            CONTEXT.del_event(DATAS.index[msg.cmds[1]]["id"])
            DATAS.delChild(DATAS.index[msg.cmds[1]])
            save()
        else:
            res.append_message("Vous ne pouvez pas terminer le compteur %s, créé par %s."% (msg.cmds[1], DATAS.index[msg.cmds[1]]["proprio"]))
        return res
    else:
        return Response(msg.sender, "%s n'est pas un compteur connu."% (msg.cmds[1]))

def liste(msg):
    msg.send_snd ("Compteurs connus : %s." % ", ".join(DATAS.index.keys()))

def parseanswer(msg):
    if msg.cmds[0] in DATAS.index:
        if DATAS.index[msg.cmds[0]].name == "strend":
            if DATAS.index[msg.cmds[0]].hasAttribute("end"):
                return Response(msg.sender, "%s commencé il y a %s et se terminera dans %s." % (msg.cmds[0], msg.just_countdown(datetime.now() - DATAS.index[msg.cmds[0]].getDate("start")), msg.just_countdown(DATAS.index[msg.cmds[0]].getDate("end") - datetime.now())), channel=msg.channel)
            else:
                return Response(msg.sender, "%s commencé il y a %s." % (msg.cmds[0], msg.just_countdown(datetime.now () - DATAS.index[msg.cmds[0]].getDate("start"))), channel=msg.channel)
        else:
            save()
            return Response(msg.sender, msg.countdown_format (DATAS.index[msg.cmds[0]].getDate("start"), DATAS.index[msg.cmds[0]]["msg_before"], DATAS.index[msg.cmds[0]]["msg_after"]), channel=msg.channel)

def parseask(msg):
  msgl = msg.content.lower()
  if re.match("^.*((create|new) +(a|an|a +new|an *other)? *(events?|commande?)|(nouvel(le)?|ajoute|cr[ée]{1,3}) +(un)? *([eé]v[ée]nements?|commande?)).*$", msgl) is not None:
    name = re.match("^.*!([^ \"'@!]+).*$", msg.content)
    if name is not None and name.group (1) not in DATAS.index:
      texts = re.match("^[^\"]*(avant|après|apres|before|after)?[^\"]*\"([^\"]+)\"[^\"]*((avant|après|apres|before|after)?.*\"([^\"]+)\".*)?$", msg.content)
      if texts is not None and texts.group (3) is not None:
        extDate = msg.extractDate ()
        if extDate is None or extDate == "":
            return Response(msg.sender, "La date de l'événement est invalide...", channel=msg.channel)
        else:
          if texts.group (1) is not None and (texts.group (1) == "après" or texts.group (1) == "apres" or texts.group (1) == "after"):
            msg_after = texts.group (2)
            msg_before = texts.group (5)
          if (texts.group (4) is not None and (texts.group (4) == "après" or texts.group (4) == "apres" or texts.group (4) == "after")) or texts.group (1) is None:
            msg_before = texts.group (2)
            msg_after = texts.group (5)

          if msg_before.find ("%s") != -1 and msg_after.find ("%s") != -1:
            evt = ModuleState("event")
            evt["server"] = msg.server
            evt["channel"] = msg.channel
            evt["proprio"] = msg.nick
            evt["sender"] = msg.sender
            evt["name"] = name.group(1)
            evt["start"] = extDate
            evt["msg_after"] = msg_after
            evt["msg_before"] = msg_before
            DATAS.addChild(evt)
            save()
            return Response(msg.sender,
                            "Nouvel événement !%s ajouté avec succès." % name.group(1),
                            msg.channel)
          else:
              return Response(msg.sender,
                              "Pour que l'événement soit valide, ajouter %s à"
                              " l'endroit où vous voulez que soit ajouté le"
                              " compte à rebours.")
      elif texts is not None and texts.group (2) is not None:
        evt = ModuleState("event")
        evt["server"] = msg.server
        evt["channel"] = msg.channel
        evt["proprio"] = msg.nick
        evt["sender"] = msg.sender
        evt["name"] = name.group(1)
        evt["msg_before"] = texts.group (2)
        DATAS.addChild(evt)
        save()
        return Response(msg.sender, "Nouvelle commande !%s ajoutée avec succès." % name.group(1))
      else:
          return Response(msg.sender, "Veuillez indiquez les messages d'attente et d'après événement entre guillemets.")
    elif name is None:
        return Response(msg.sender, "Veuillez attribuer une commande à l'événement.")
    else:
        return Response(msg.sender, "Un événement portant ce nom existe déjà.")
