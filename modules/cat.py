"""Concatenate commands"""

# PYTHON STUFFS #######################################################

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.message import Command, DirectAsk, Text

from nemubot.module.more import Response


# MODULE CORE #########################################################

def cat(msg, *terms):
    res = Response(channel=msg.to_response, server=msg.server)
    for term in terms:
        m = context.subparse(msg, term)
        if isinstance(m, Command) or isinstance(m, DirectAsk):
            for r in context.subtreat(m):
                if isinstance(r, Response):
                    for t in range(len(r.messages)):
                        res.append_message(r.messages[t],
                                           title=r.rawtitle if not isinstance(r.rawtitle, list) else r.rawtitle[t])

                elif isinstance(r, Text):
                    res.append_message(r.message)

                elif isinstance(r, str):
                    res.append_message(r)

        else:
            res.append_message(term)

    return res


# MODULE INTERFACE ####################################################

@hook.command("cat",
              help="Concatenate responses of commands given as argument",
              help_usage={"!SUBCMD [!SUBCMD [...]]": "Concatenate response of subcommands"},
              keywords={
                  "merge": "Merge messages into the same",
              })
def cmd_cat(msg):
    if len(msg.args) < 1:
        raise IMException("No subcommand to concatenate")

    r = cat(msg, *msg.args)

    if "merge" in msg.kwargs and len(r.messages) > 1:
        r.messages = [ r.messages ]

    return r
