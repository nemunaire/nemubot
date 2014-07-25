# coding=utf-8

import subprocess
import re
import os

nemubotversion = 3.3

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_man, "MAN"))
    add_hook("cmd_hook", Hook(cmd_whatis, "man"))

def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "Read manual pages on IRC"

def help_full ():
    return "!man [0-9] /what/: gives informations about /what/."

RGXP_s = re.compile(b'\x1b\\[[0-9]+m')

def cmd_man(msg):
    args = ["man"]
    num = None
    if len(msg.cmds) == 2:
        args.append(msg.cmds[1])
    elif len(msg.cmds) >= 3:
        try:
            num = int(msg.cmds[1])
            args.append("%d" % num)
            args.append(msg.cmds[2])
        except ValueError:
            args.append(msg.cmds[1])

    os.unsetenv("LANG")
    res = Response(msg.sender, channel=msg.channel)
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        for line in proc.stdout.read().split(b"\n"):
            (line, n) = RGXP_s.subn(b'', line)
            res.append_message(line.decode())

    if len(res.messages) <= 0:
        if num is not None:
            res.append_message("Il n'y a pas d'entrée %s dans la section %d du manuel." % (msg.cmds[1], num))
        else:
            res.append_message("Il n'y a pas de page de manuel pour %s." % msg.cmds[1])

    return res

def cmd_whatis(msg):
    args = ["whatis", " ".join(msg.cmds[1:])]

    res = Response(msg.sender, channel=msg.channel)
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        for line in proc.stdout.read().split(b"\n"):
            (line, n) = RGXP_s.subn(b'', line)
            res.append_message(" ".join(line.decode().split()))

    if len(res.messages) <= 0:
        if num is not None:
            res.append_message("Il n'y a pas d'entrée %s dans la section %d du manuel." % (msg.cmds[1], num))
        else:
            res.append_message("Il n'y a pas de page de manuel pour %s." % msg.cmds[1])

    return res
