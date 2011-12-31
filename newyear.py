# coding=utf-8
import re
import os
from datetime import datetime
import time

def launch(s, chan, msgpart):
    #What is the next year?
    nyear = datetime.today().year + 1;

    if msgpart != 0 and len(msgpart) > 1:
        os.environ['TZ'] = msgpart[1]
        time.tzset()

    sentence_c = "PRIVMSG " + chan + " :"

    #Calculate time before new year
    if datetime.now() > datetime(nyear, 1, 1, 0, 0, 1):
        sentence_c += "Nous faisons déjà la fête depuis{0}"
        delta = datetime.now() - datetime(nyear, 1, 1, 0, 0, 1)

    else:
        sentence_c += "Il reste{0} avant la nouvelle année"
        delta = datetime(nyear, 1, 1, 0, 0, 1) - datetime.now()

    sec = delta.seconds
    hours, remainder = divmod(sec, 3600)
    minutes, seconds = divmod(remainder, 60)

    sentence = ""
    force = 0

    if force or delta.days > 0:
        force = 1
        sentence += " {0} jour".format(delta.days)

        if delta.days > 1:
            sentence += "s"
        sentence += ","

    if force or hours > 0:
        force = 1
        sentence += " {0} heure".format(hours)
        if hours > 1:
            sentence += "s"
        sentence += ","

    if force or minutes > 0:
        force = 1
        sentence += " {0} minute".format(minutes)
        if minutes > 1:
            sentence += "s"
        sentence += " et"

    if force or seconds > 0:
        force = 1
        sentence += " {0} seconde".format(seconds)
        if seconds > 1:
            sentence += "s"

    s.send(sentence_c.format(sentence) + "\r\n")

    if msgpart != 0 and len(msgpart) > 1:
        os.environ['TZ'] = "Europe/Paris"

def special(s, chan):
    s.send("PRIVMSG {0} :Bonne année {1} !\r\n".format(chan, datetime.today().year))
