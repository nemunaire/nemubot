"""Help to make choice"""

# PYTHON STUFFS #######################################################

import random
import shlex

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook

from more import Response


# MODULE INTERFACE ####################################################

@hook.command("choice")
def cmd_choice(msg):
    if not len(msg.args):
        raise IMException("indicate some terms to pick!")

    return Response(random.choice(msg.args),
                    channel=msg.channel,
                    nick=msg.frm)


@hook.command("choicecmd")
def cmd_choicecmd(msg):
    if not len(msg.args):
        raise IMException("indicate some command to pick!")

    choice = shlex.split(random.choice(msg.args))

    return [x for x in context.subtreat(context.subparse(msg, choice))]


@hook.command("choiceres")
def cmd_choiceres(msg):
    if not len(msg.args):
        raise IMException("indicate some command to pick a message from!")

    rl = [x for x in context.subtreat(context.subparse(msg, " ".join(msg.args)))]
    if len(rl) <= 0:
        return rl

    r = random.choice(rl)

    if isinstance(r, Response):
        for i in range(len(r.messages) - 1, -1, -1):
            if isinstance(r.messages[i], list):
                r.messages = [ random.choice(random.choice(r.messages)) ]
            elif isinstance(r.messages[i], str):
                r.messages = [ random.choice(r.messages) ]
    return r
