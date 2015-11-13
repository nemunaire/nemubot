"""Filter messages, displaying lines matching a pattern"""

# PYTHON STUFFS #######################################################

import re

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.message import Command, Text

from more import Response


# MODULE CORE #########################################################

def grep(fltr, cmd, args, msg):
    """Perform a grep like on known nemubot structures

    Arguments:
    fltr -- The filter regexp
    cmd -- The subcommand to execute
    args -- subcommand arguments
    msg -- The original message
    """

    for r in context.subtreat(Command(cmd,
                                      args,
                                      to_response=msg.to_response,
                                      frm=msg.frm,
                                      server=msg.server)):
        if isinstance(r, Response):
            for i in range(len(r.messages) - 1, -1, -1):
                if isinstance(r.messages[i], list):
                    for j in range(len(r.messages[i]) - 1, -1, -1):
                        if not re.match(fltr, r.messages[i][j]):
                            r.messages[i].pop(j)
                    if len(r.messages[i]) <= 0:
                        r.messages.pop(i)
                elif isinstance(r.messages[i], str) and not re.match(fltr, r.messages[i]):
                    r.messages.pop(i)
            yield r

        elif isinstance(r, Text):
            if re.match(fltr, r.message):
                yield r

        else:
            yield r


# MODULE INTERFACE ####################################################

@hook.command("grep",
              help="Display only lines from a subcommand matching the given pattern",
              help_usage={"PTRN !SUBCMD": "Filter SUBCMD command using the pattern PTRN"})
def cmd_grep(msg):
    if len(msg.args) < 2:
        raise IMException("Please provide a filter and a command")

    return [m for m in grep(msg.args[0] if msg.args[0][0] == "^" else ".*" + msg.args[0] + ".*",
                            msg.args[1][1:] if msg.args[1][0] == "!" else msg.args[1],
                            msg.args[2:],
                            msg)]
