# coding=utf-8

from datetime import datetime
from datetime import timedelta
from urllib.parse import quote

from tools import web

nemubotversion = 3.3

def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "Gets informations about current and next Épita courses"

def help_full ():
    return "!chronos [spé] : gives current and next courses."


def get_courses(classe=None, room=None, teacher=None, date=None):
    url = CONF.getNode("server")["url"]
    if classe is not None:
        url += "&class=" + quote(classe)
    if room is not None:
        url += "&room=" + quote(room)
    if teacher is not None:
        url += "&teacher=" + quote(teacher)
    #TODO: date, not implemented at 23.tf

    response = web.getXML(url)
    if response is not None:
        return response.getNodes("course")
    else:
        return None

def get_next_courses(classe=None, room=None, teacher=None, date=None):
    courses = get_courses(classe, room, teacher, date)
    now = datetime.now()
    for c in courses:
        start = c.getFirstNode("start").getDate()

        if now > start:
            return c
    return None

def get_near_courses(classe=None, room=None, teacher=None, date=None):
    courses = get_courses(classe, room, teacher, date)
    return courses[0]

def cmd_chronos(msg):
    if len(msg.cmds) > 1:
        classe = msg.cmds[1]
    else:
        classe = ""

    res = Response(msg.sender, channel=msg.channel, nomore="Je n'ai pas d'autre cours à afficher")

    courses = get_courses(classe)
    if courses is not None:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        for c in courses:
            idc      = c.getFirstNode("id").getContent()
            crs      = c.getFirstNode("title").getContent()
            start    = c.getFirstNode("start").getDate()
            end      = c.getFirstNode("end").getDate()
            where    = c.getFirstNode("where").getContent()
            teacher  = c.getFirstNode("teacher").getContent()
            students = c.getFirstNode("students").getContent()

            if now > start:
                title = "Actuellement "
                msg = "\x03\x02" + crs + "\x03\x02 jusqu'"
                if end < tomorrow:
                    msg += "à \x03\x02" + end.strftime("%H:%M")
                else:
                    msg += "au \x03\x02" + end.strftime("%a %d à %H:%M")
                msg += "\x03\x02 en \x03\x02" + where + "\x03\x02"
            else:
                title = "Prochainement "
                duration = (end - start).total_seconds() / 60

                msg = "\x03\x02" + crs + "\x03\x02 le \x03\x02" + end.strftime("%a %d à %H:%M") + "\x03\x02 pour " + "%dh%02d" % (int(duration / 60), duration % 60) + " en \x03\x02" + where + "\x03\x02"

            if teacher != "":
                msg += " avec " + teacher
            if students != "":
                msg += " pour les " + students

            res.append_message(msg, title)
    else:
        res.append_message("Aucun cours n'a été trouvé")

    return res
