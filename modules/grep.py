"""Filter messages, displaying lines matching a pattern"""

# PYTHON STUFFS #######################################################

import re

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.message import Command, Text

from more import Response


# MODULE CORE #########################################################

def grep(fltr, cmd, args, msg, icase=False, only=False):
    """Perform a grep like on known nemubot structures

    Arguments:
    fltr -- The filter regexp
    cmd -- The subcommand to execute
    args -- subcommand arguments
    msg -- The original message
    icase -- like the --ignore-case parameter of grep
    only -- like the --only-matching parameter of grep
    """

    fltr = re.compile(fltr, re.I if icase else 0)

    for r in context.subtreat(Command(cmd,
                                      args,
                                      to_response=msg.to_response,
                                      frm=msg.frm,
                                      server=msg.server)):
        if isinstance(r, Response):
            for i in range(len(r.messages) - 1, -1, -1):
                if isinstance(r.messages[i], list):
                    for j in range(len(r.messages[i]) - 1, -1, -1):
                        res = fltr.match(r.messages[i][j])
                        if not res:
                            r.messages[i].pop(j)
                        elif only:
                            r.messages[i][j] = res.group(1) if fltr.groups else res.group(0)
                    if len(r.messages[i]) <= 0:
                        r.messages.pop(i)
                elif isinstance(r.messages[i], str):
                    res = fltr.match(r.messages[i])
                    if not res:
                        r.messages.pop(i)
                    elif only:
                        r.messages[i] = res.group(1) if fltr.groups else res.group(0)
            yield r

        elif isinstance(r, Text):
            res = fltr.match(r.message)
            if res:
                if only:
                    r.message = res.group(1) if fltr.groups else res.group(0)
                yield r

        else:
            yield r


# MODULE INTERFACE ####################################################

@hook.command("grep",
              help="Display only lines from a subcommand matching the given pattern",
              help_usage={"PTRN !SUBCMD": "Filter SUBCMD command using the pattern PTRN"},
              keywords={
                  "nocase": "Perform case-insensitive matching",
                  "only": "Print only the matched parts of a matching line",
              })
def cmd_grep(msg):
    if len(msg.args) < 2:
        raise IMException("Please provide a filter and a command")

    only = "only" in msg.kwargs

    l = [m for m in grep(msg.args[0] if msg.args[0][0] == "^" else ".*?(" + msg.args[0] + ").*?",
                         msg.args[1][1:] if msg.args[1][0] == "!" else msg.args[1],
                         msg.args[2:],
                         msg,
                         icase="nocase" in msg.kwargs,
                         only=only) if m is not None]

    if len(l) <= 0:
        raise IMException("Pattern not found in output")

    return l
