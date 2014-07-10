# coding=utf-8

import random

nemubotversion = 3.3

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_choice, "choice"))

def cmd_choice(msg):
    return Response(msg.sender, random.choice(msg.cmds[1:]), channel=msg.channel, nick=msg.nick)
