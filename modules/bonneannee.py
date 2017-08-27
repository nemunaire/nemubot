"""Wishes Happy New Year when the time comes"""

# PYTHON STUFFS #######################################################

from datetime import datetime, timezone

from nemubot.hooks import hook
from nemubot.tools.countdown import countdown_format

from nemubot.module.more import Response


# GLOBALS #############################################################

yr = datetime.now(timezone.utc).year
yrn = datetime.now(timezone.utc).year + 1


# LOADING #############################################################

def load(context):
    if not context.config or not context.config.hasNode("sayon"):
        print("You can append in your configuration some balise to "
              "automaticaly wish an happy new year on some channels like:\n"
              "<sayon hostid=\"nemubot@irc.freenode.net:6667\" "
              "channel=\"#nemutest\" />")

    def bonneannee():
        txt = "Bonne année %d !" % yrn
        print(txt)
        if context.config and context.config.hasNode("sayon"):
            for sayon in context.config.getNodes("sayon"):
                if "hostid" not in sayon or "channel" not in sayon:
                    print("Error: missing hostif or channel")
                    continue
                srv = sayon["hostid"]
                chan = sayon["channel"]
                context.send_response(srv, Response(txt, chan))

    d = datetime(yrn, 1, 1, 0, 0, 0, 0,
                 timezone.utc) - datetime.now(timezone.utc)
    context.add_event(ModuleEvent(interval=0, offset=d.total_seconds(),
                                  call=bonneannee))


# MODULE INTERFACE ####################################################

@hook.command("newyear",
      help="Display the remaining time before the next new year")
@hook.command(str(yrn),
      help="Display the remaining time before %d" % yrn)
def cmd_newyear(msg):
    return Response(countdown_format(datetime(yrn, 1, 1, 0, 0, 1, 0,
                                              timezone.utc),
                                     "Il reste %s avant la nouvelle année.",
                                     "Nous faisons déjà la fête depuis %s !"),
                    channel=msg.channel)


@hook.command(data=yrn, regexp="^[0-9]{4}$",
      help="Calculate time remaining/passed before/since the requested year")
def cmd_timetoyear(msg, cur):
    yr = int(msg.cmd)

    if yr == cur:
        return None

    return Response(countdown_format(datetime(yr, 1, 1, 0, 0, 1, 0,
                                              timezone.utc),
                                     "Il reste %s avant %d." % ("%s", yr),
                                     "Le premier janvier %d est passé "
                                     "depuis %s !" % (yr, "%s")),
                    channel=msg.channel)
