# coding=utf-8

from datetime import datetime

nemubotversion = 3.3

def load(context):
    yr = datetime.today().year
    yrn = datetime.today().year + 1

    d = datetime(yrn, 1, 1, 0, 0, 0) - datetime.now()
#    d = datetime(yr, 12, 31, 19, 34, 0) - datetime.now()
    add_event(ModuleEvent(intervalle=0, offset=d.total_seconds(), call=bonneannee))

    from hooks import Hook
    add_hook("cmd_rgxp", Hook(cmd_timetoyear, data=yrn, regexp="[0-9]{4}"))
    add_hook("cmd_hook", Hook(cmd_newyear, str(yrn), yrn))
    add_hook("cmd_hook", Hook(cmd_newyear, "ny", yrn))
    add_hook("cmd_hook", Hook(cmd_newyear, "newyear", yrn))
    add_hook("cmd_hook", Hook(cmd_newyear, "new-year", yrn))
    add_hook("cmd_hook", Hook(cmd_newyear, "new year", yrn))

def bonneannee():
    txt = "Bonne année %d !" % datetime.today().year
    print (txt)
    send_response("localhost:2771", Response(None, txt, "#epitagueule"))
    send_response("localhost:2771", Response(None, txt, "#yaka"))
    send_response("localhost:2771", Response(None, txt, "#epita2014"))
    send_response("localhost:2771", Response(None, txt, "#ykar"))
    send_response("localhost:2771", Response(None, txt, "#ordissimo"))
    send_response("localhost:2771", Response(None, txt, "#42sh"))
    send_response("localhost:2771", Response(None, txt, "#nemubot"))

def cmd_newyear(msg, yr):
    return Response(msg.sender,
        msg.countdown_format(datetime(yr, 1, 1, 0, 0, 1),
                             "Il reste %s avant la nouvelle année.",
                             "Nous faisons déjà la fête depuis %s !"),
                    channel=msg.channel)

def cmd_timetoyear(msg, cur):
    yr = int(msg.cmds[0])

    if yr == cur:
        return None

    return Response(msg.sender,
        msg.countdown_format(datetime(yr, 1, 1, 0, 0, 1),
                             "Il reste %s avant %d." % ("%s", yr),
                             "Le premier janvier %d est passé depuis %s !" % (yr, "%s")),
                    channel=msg.channel)
