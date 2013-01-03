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


def cmd_chronos(msg):
    url = CONF.getNode("server")["url"]
    if len(msg.cmds) > 1:
        url += "&class=" + quote(msg.cmds[1])

    res = Response(msg.sender, channel=msg.channel, nomore="Je n'ai pas d'autre cours à afficher")
    response = web.getXML(url)
    if response is not None:
        courses = response.getNodes("course")
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
