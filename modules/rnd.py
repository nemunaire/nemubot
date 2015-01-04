# coding=utf-8

"""Help to make choice"""

import random

from nemubot.exception import IRCException
from nemubot.hooks import hook

nemubotversion = 3.4

from more import Response


@hook("cmd_hook", "choice")
def cmd_choice(msg):
    if len(msg.cmds) > 1:
        return Response(random.choice(msg.cmds[1:]),
                        channel=msg.channel,
                        nick=msg.nick)
    else:
        raise IRCException("indicate some terms to pick!")
