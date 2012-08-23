# coding=utf-8

import imp
import re
import sys
from datetime import timedelta
from datetime import datetime
import time
import threading

nemubotversion = 3.2

from event import ModuleEvent
from hooks import Hook
from xmlparser.node import ModuleState

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
            context.add_event(event)

def fini(strend):
    for server in CONTEXT.servers.keys():
        if not strend.hasAttribute("server") or server == strend["server"]:
            if strend["channel"] == CONTEXT.servers[server].nick:
                CONTEXT.servers[server].send_msg_usr(strend["proprio"], "%s: %s arrivé à échéance." % (strend["proprio"], strend["name"]))
            else:
                CONTEXT.servers[server].send_msg(strend["channel"], "%s: %s arrivé à échéance." % (strend["proprio"], strend["name"]))
    DATAS.delChild(DATAS.index[strend["name"]])
    save()

def cmd_we(msg):
    ndate = datetime.today() + timedelta(5 - datetime.today().weekday())
    ndate = datetime(ndate.year, ndate.month, ndate.day, 0, 0, 1)
    msg.send_chn (
        msg.countdown_format (ndate,
                              "Il reste %s avant le week-end, courage ;)",
                              "Youhou, on est en week-end depuis %s."))

def cmd_newyear(msg):
    msg.send_chn (
        msg.countdown_format (datetime(datetime.today().year + 1, 1, 1, 0, 0, 1),
                              "Il reste %s avant la nouvelle année.",
                              "Nous faisons déjà la fête depuis %s !"))

def cmd_vacances(msg):
    msg.send_chn (
        msg.countdown_format (datetime(2012, 7, 30, 18, 0, 1),
                              "Il reste %s avant les vacances :)",
                              "Profitons, c'est les vacances depuis %s."))

def start_countdown(msg):
    if msg.cmd[1] not in DATAS:

        strnd = ModuleState("strend")
        strnd["server"] = msg.srv.id
        strnd["channel"] = msg.channel
        strnd["proprio"] = msg.nick
        strnd["start"] = datetime.now()
        strnd["name"] = msg.cmd[1]
        DATAS.addChild(strnd)

        evt = ModuleEvent(call=fini, call_data=dict(strend=strnd))

        if len(msg.cmd) > 2:
            result = re.match("([0-9]+)([smhdjSMHDJ])?", msg.cmd[2])
            if result is not None:
                try:
                    if result.group(2) is not None and (result.group(2) == "m" or result.group(2) == "M"):
                        strnd["end"] = datetime.now() + timedelta(minutes=int(result.group(1)))
                    elif result.group(2) is not None and (result.group(2) == "h" or result.group(2) == "H"):
                        strnd["end"] = datetime.now() + timedelta(hours=int(result.group(1)))
                    elif result.group(2) is not None and (result.group(2) == "d" or result.group(2) == "D" or result.group(2) == "j" or result.group(2) == "J"):
                        strnd["end"] = datetime.now() + timedelta(days=int(result.group(1)))
                    else:
                        strnd["end"] = datetime.now() + timedelta(seconds=int(result.group(1)))
                    evt.end = strnd.getDate("end")
                    CONTEXT.add_event(evt)
                    msg.send_snd ("%s commencé le %s et se terminera le %s."% (msg.cmd[1], datetime.now(), strnd.getDate("end")))
                except:
                    msg.send_snd ("Impossible de définir la fin de %s."% (msg.cmd[1]))
                    msg.send_snd ("%s commencé le %s."% (msg.cmd[1], datetime.now()))
            else:
                msg.send_snd ("%s commencé le %s"% (msg.cmd[1], datetime.now()))
        save()
    else:
        msg.send_snd ("%s existe déjà."% (msg.cmd[1]))
    return True

def end_countdown(msg):
    if msg.cmd[1] in DATAS.index:
        msg.send_chn ("%s a duré %s." % (msg.cmd[1], msg.just_countdown(datetime.now () - DATAS.index[msg.cmd[1]].getDate("start"))))
        if DATAS.index[msg.cmd[1]]["proprio"] == msg.nick or (msg.cmd[0] == "forceend" and msg.nick == msg.srv.owner):
            DATAS.delChild(DATAS.index[msg.cmd[1]])
            Manager.newStrendEvt.set()
            save()
        else:
            msg.send_snd ("Vous ne pouvez pas terminer le compteur %s, créé par %s."% (msg.cmd[1], DATAS.index[msg.cmd[1]]["proprio"]))
    else:
        msg.send_snd ("%s n'est pas un compteur connu."% (msg.cmd[1]))
    return True

def liste(msg):
    msg.send_snd ("Compteurs connus : %s." % ", ".join(DATAS.index.keys()))

def parseanswer(msg):
    if msg.cmd[0] in DATAS.index:
        if DATAS.index[msg.cmd[0]].name == "strend":
            if DATAS.index[msg.cmd[0]].hasAttribute("end"):
                msg.send_chn ("%s commencé il y a %s et se terminera dans %s." % (msg.cmd[0], msg.just_countdown(datetime.now() - DATAS.index[msg.cmd[0]].getDate("start")), msg.just_countdown(DATAS.index[msg.cmd[0]].getDate("end") - datetime.now())))
            else:
                msg.send_chn ("%s commencé il y a %s." % (msg.cmd[0], msg.just_countdown(datetime.now () - DATAS.index[msg.cmd[0]].getDate("start"))))
        else:
            msg.send_chn (msg.countdown_format (DATAS.index[msg.cmd[0]].getDate("start"), DATAS.index[msg.cmd[0]]["msg_before"], DATAS.index[msg.cmd[0]]["msg_after"]))
            save()
        return True
    return False

def parseask(msg):
  msgl = msg.content.lower()
  if re.match("^.*((create|new) +(a|an|a +new|an *other)? *(events?|commande?)|(nouvel(le)?|ajoute|cr[ée]{1,3}) +(un)? *([eé]v[ée]nements?|commande?)).*$", msgl) is not None:
    name = re.match("^.*!([^ \"'@!]+).*$", msg.content)
    if name is not None and name.group (1) not in DATAS.index:
      texts = re.match("^[^\"]*(avant|après|apres|before|after)?[^\"]*\"([^\"]+)\"[^\"]*((avant|après|apres|before|after)?.*\"([^\"]+)\".*)?$", msg.content)
      if texts is not None and texts.group (3) is not None:
        extDate = msg.extractDate ()
        if extDate is None or extDate == "":
          msg.send_snd ("La date de l'événement est invalide...")
        else:
          if texts.group (1) is not None and (texts.group (1) == "après" or texts.group (1) == "apres" or texts.group (1) == "after"):
            msg_after = texts.group (2)
            msg_before = texts.group (5)
          if (texts.group (4) is not None and (texts.group (4) == "après" or texts.group (4) == "apres" or texts.group (4) == "after")) or texts.group (1) is None:
            msg_before = texts.group (2)
            msg_after = texts.group (5)

          if msg_before.find ("%s") != -1 and msg_after.find ("%s") != -1:
            evt = ModuleState("event")
            evt["server"] = msg.srv.id
            evt["channel"] = msg.channel
            evt["proprio"] = msg.nick
            evt["name"] = name.group(1)
            evt["start"] = extDate
            evt["msg_after"] = msg_after
            evt["msg_before"] = msg_before
            DATAS.addChild(evt)
            save()
            msg.send_snd ("Nouvel événement !%s ajouté avec succès."%name.group (1))
          else:
            msg.send_snd ("Pour que l'événement soit valide, ajouter %s à l'endroit où vous voulez que soit ajouté le compte à rebours.")
      elif texts is not None and texts.group (2) is not None:
        evt = ModuleState("event")
        evt["server"] = msg.srv.id
        evt["channel"] = msg.channel
        evt["proprio"] = msg.nick
        evt["name"] = name.group(1)
        evt["msg_before"] = texts.group (2)
        DATAS.addChild(evt)
        save()
        msg.send_snd ("Nouvelle commande !%s ajoutée avec succès."%name.group (1))
      else:
        msg.send_snd ("Veuillez indiquez les messages d'attente et d'après événement entre guillemets.")
    elif name is None:
      msg.send_snd ("Veuillez attribuer une commande à l'événement.")
    else:
      msg.send_snd ("Un événement portant ce nom existe déjà.")
  return False
