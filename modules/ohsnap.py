"""ohsnap.p0m.fr related module"""

# PYTHON STUFFS #######################################################

from functools import partial
import json

from nemubot import context
from nemubot.event import ModuleEvent
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools.web import getJSON
from nemubot.tools.xmlparser.node import ModuleState

from nemubot.module.more import Response


# LOADING #############################################################

def load(context):
    for wn in context.data.getNodes("alert_channel"):
        _ticker(**wn.attributes)


# MODULE CORE #########################################################

last_seen = None

def _ticker(to_server, to_channel, **kwargs):
    global last_seen
    context.add_event(ModuleEvent(call=partial(_ticker, to_server, to_channel, **kwargs), interval=42))
    last = getJSON("https://ohsnap.p0m.fr/api/images/last")
    if last["hash"] != last_seen:
        if last_seen is not None:
            context.send_response(to_server, Response("Nouveau snap de {author} : https://ohsnap.p0m.fr/{hash}".format(**last), channel=to_channel))
        last_seen = last["hash"]


# MODULE INTERFACE ####################################################

@hook.command("snap", help="retrieve the latest image posted on ohsnap.p0m.fr")
def cmd_snap(msg):
    images = getJSON("https://ohsnap.p0m.fr/api/images")

    if "errmsg" in images:
        raise IMException(images["errmsg"])

    res = Response(channel=msg.channel, nomore="No more snap to show")
    for image in images:
        res.append_message("Snap de {author}, le {upload_time} : https://ohsnap.p0m.fr/{hash}".format(**image))
    return res

@hook.command("ohsnap_watch",
              help="Launch an event looking for new images on ohsnap")
def cmd_watch(msg):
    if not msg.frm_owner:
        raise IMException("sorry, this command is currently limited to the owner")

    wnnode = ModuleState("alert_channel")
    wnnode["to_server"] = msg.server
    wnnode["to_channel"] = msg.channel
    wnnode["owner"] = msg.frm

    context.data.addChild(wnnode)
    watch(**wnnode.attributes)

    return Response("Ok ok, I'll alert you on new pictures on ohsnap!", channel=msg.channel)
