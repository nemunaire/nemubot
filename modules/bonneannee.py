# coding=utf-8

"""Wishes Happy New Year when the time comes"""

from datetime import datetime, timezone

from nemubot.hooks import hook
from nemubot.tools.countdown import countdown_format

nemubotversion = 3.4

from more import Response

yr = datetime.now(timezone.utc).year
yrn = datetime.now(timezone.utc).year + 1


def load(context):
    if not CONF or not CONF.hasNode("sayon"):
        print("You can append in your configuration some balise to "
              "automaticaly wish an happy new year on some channels like:\n"
              "<sayon hostid=\"nemubot@irc.freenode.net:6667\" "
              "channel=\"#nemutest\" />")

    def bonneannee():
        txt = "Bonne année %d !" % yrn
        print(txt)
        if CONF and CONF.hasNode("sayon"):
            for sayon in CONF.getNodes("sayon"):
                if "hostid" not in sayon or "channel" not in sayon:
                    print("Error: missing hostif or channel")
                    continue
                srv = sayon["hostid"]
                chan = sayon["channel"]
                send_response(srv, Response(txt, chan))

    d = datetime(yrn, 1, 1, 0, 0, 0, 0,
                 timezone.utc) - datetime.now(timezone.utc)
    add_event(ModuleEvent(interval=0, offset=d.total_seconds(),
                          call=bonneannee))


@hook("cmd_hook", "newyear")
@hook("cmd_hook", str(yrn), yrn)
def cmd_newyear(msg, yr):
    return Response(countdown_format(datetime(yr, 1, 1, 0, 0, 1, 0,
                                              timezone.utc),
                                     "Il reste %s avant la nouvelle année.",
                                     "Nous faisons déjà la fête depuis %s !"),
                    channel=msg.channel)


@hook("cmd_rgxp", data=yrn, regexp="^[0-9]{4}$")
def cmd_timetoyear(msg, cur):
    yr = int(msg.cmds[0])

    if yr == cur:
        return None

    return Response(countdown_format(datetime(yr, 1, 1, 0, 0, 1, 0,
                                              timezone.utc),
                                     "Il reste %s avant %d." % ("%s", yr),
                                     "Le premier janvier %d est passé "
                                     "depuis %s !" % (yr, "%s")),
                    channel=msg.channel)
