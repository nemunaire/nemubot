# coding=utf-8

import random

from hooks import hook

nemubotversion = 3.4

@hook("cmd_hook", "choice")
def cmd_choice(msg):
    if len(msg.cmds) > 1:
        return Response(msg.sender, random.choice(msg.cmds[1:]), channel=msg.channel, nick=msg.nick)
    else:
        raise IRCException("indicate some terms to pick!")
