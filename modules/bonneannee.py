# coding=utf-8

from datetime import datetime

from hooks import hook

nemubotversion = 3.3

yr = datetime.today().year
yrn = datetime.today().year + 1

def load(context):
    d = datetime(yrn, 1, 1, 0, 0, 0) - datetime.now()
    add_event(ModuleEvent(intervalle=0, offset=d.total_seconds(), call=bonneannee))

def bonneannee():
    txt = "Bonne année %d !" % datetime.today().year
    print (txt)
    send_response("localhost:2771", Response(None, txt, "#epitagueule"))
    send_response("localhost:2771", Response(None, txt, "#yaka"))
    send_response("localhost:2771", Response(None, txt, "#epita2014"))
    send_response("localhost:2771", Response(None, txt, "#ykar"))
    send_response("localhost:2771", Response(None, txt, "#42sh"))
    send_response("localhost:2771", Response(None, txt, "#nemubot"))

@hook("cmd_hook", "newyear")
@hook("cmd_hook", str(yrn), yrn)
def cmd_newyear(msg, yr):
    return Response(msg.sender,
        msg.countdown_format(datetime(yr, 1, 1, 0, 0, 1),
                             "Il reste %s avant la nouvelle année.",
                             "Nous faisons déjà la fête depuis %s !"),
                    channel=msg.channel)

@hook("cmd_rgxp", data=yrn, regexp="^[0-9]{4}$")
def cmd_timetoyear(msg, cur):
    yr = int(msg.cmds[0])

    if yr == cur:
        return None

    return Response(msg.sender,
        msg.countdown_format(datetime(yr, 1, 1, 0, 0, 1),
                             "Il reste %s avant %d." % ("%s", yr),
                             "Le premier janvier %d est passé depuis %s !" % (yr, "%s")),
                    channel=msg.channel)
