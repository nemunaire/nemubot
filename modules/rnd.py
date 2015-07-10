# coding=utf-8

"""Help to make choice"""

import random

from nemubot.exception import IRCException
from nemubot.hooks import hook

nemubotversion = 3.4

from more import Response


@hook("cmd_hook", "choice")
def cmd_choice(msg):
    if not len(msg.args):
        raise IRCException("indicate some terms to pick!")

    return Response(random.choice(msg.args),
                    channel=msg.channel,
                    nick=msg.nick)
