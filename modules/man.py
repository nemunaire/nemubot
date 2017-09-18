"""Read manual pages on IRC"""

# PYTHON STUFFS #######################################################

import subprocess
import re
import os

from nemubot.hooks import hook

from nemubot.module.more import Response


# GLOBALS #############################################################

RGXP_s = re.compile(b'\x1b\\[[0-9]+m')


# MODULE INTERFACE ####################################################

@hook.command("MAN",
              help="Show man pages",
              help_usage={
                  "SUBJECT": "Display the default man page for SUBJECT",
                  "SECTION SUBJECT": "Display the man page in SECTION for SUBJECT"
              })
def cmd_man(msg):
    args = ["man"]
    num = None
    if len(msg.args) == 1:
        args.append(msg.args[0])
    elif len(msg.args) >= 2:
        try:
            num = int(msg.args[0])
            args.append("%d" % num)
            args.append(msg.args[1])
        except ValueError:
            args.append(msg.args[0])

    os.unsetenv("LANG")
    res = Response(channel=msg.channel)
    with subprocess.Popen(args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE) as proc:
        for line in proc.stdout.read().split(b"\n"):
            (line, n) = RGXP_s.subn(b'', line)
            res.append_message(line.decode())

    if len(res.messages) <= 0:
        if num is not None:
            res.append_message("There is no entry %s in section %d." %
                               (msg.args[0], num))
        else:
            res.append_message("There is no man page for %s." % msg.args[0])

    return res


@hook.command("man",
              help="Show man pages synopsis (in one line)",
              help_usage={
                  "SUBJECT": "Display man page synopsis for SUBJECT",
              })
def cmd_whatis(msg):
    args = ["whatis", " ".join(msg.args)]

    res = Response(channel=msg.channel)
    with subprocess.Popen(args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE) as proc:
        for line in proc.stdout.read().split(b"\n"):
            (line, n) = RGXP_s.subn(b'', line)
            res.append_message(" ".join(line.decode().split()))

    if len(res.messages) <= 0:
        res.append_message("There is no man page for %s." % msg.args[0])

    return res
