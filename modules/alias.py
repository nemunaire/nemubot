# coding=utf-8

"""Create alias of commands"""

import re
import sys
from datetime import datetime, timezone
import shlex

from nemubot import context
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.message import Command
from nemubot.tools.xmlparser.node import ModuleState

nemubotversion = 3.4

from more import Response


def load(context):
    """Load this module"""
    if not context.data.hasNode("aliases"):
        context.data.addChild(ModuleState("aliases"))
    context.data.getNode("aliases").setIndex("alias")
    if not context.data.hasNode("variables"):
        context.data.addChild(ModuleState("variables"))
    context.data.getNode("variables").setIndex("name")


def set_variable(name, value, creator):
    var = ModuleState("variable")
    var["name"] = name
    var["value"] = value
    var["creator"] = creator
    context.data.getNode("variables").addChild(var)


def get_variable(name, msg=None):
    if name == "sender" or name == "from" or name == "nick":
        return msg.frm
    elif name == "chan" or name == "channel":
        return msg.channel
    elif name == "date":
        return datetime.now(timezone.utc).strftime("%c")
    elif name in context.data.getNode("variables").index:
        return context.data.getNode("variables").index[name]["value"]
    else:
        return ""


@hook("cmd_hook", "set")
def cmd_set(msg):
    if len(msg.args) < 2:
        raise IRCException("!set prend au minimum deux arguments : "
                           "le nom de la variable et sa valeur.")
    set_variable(msg.args[0], " ".join(msg.args[1:]), msg.nick)
    context.save()
    return Response("Variable \$%s définie." % msg.args[0],
                    channel=msg.channel)


@hook("cmd_hook", "listalias")
def cmd_listalias(msg):
    if len(msg.args):
        res = list()
        for user in msg.args:
            als = [x["alias"] for x in context.data.getNode("aliases").index.values() if x["creator"] == user]
            if len(als) > 0:
                res.append("%s's aliases: %s" % (user, ", ".join(als)))
            else:
                res.append("%s has never created aliases." % user)
        return Response("; ".join(res), channel=msg.channel)
    elif len(context.data.getNode("aliases").index):
        return Response("Known aliases: %s." %
                        ", ".join(context.data.getNode("aliases").index.keys()),
                        channel=msg.channel)
    else:
        return Response("There is no alias currently.", channel=msg.channel)


@hook("cmd_hook", "listvars")
def cmd_listvars(msg):
    if len(msg.args):
        res = list()
        for user in msg.args:
            als = [x["alias"] for x in context.data.getNode("variables").index.values() if x["creator"] == user]
            if len(als) > 0:
                res.append("Variables créées par %s : %s" % (user, ", ".join(als)))
            else:
                res.append("%s n'a pas encore créé de variable" % user)
        return Response(" ; ".join(res), channel=msg.channel)
    elif len(context.data.getNode("variables").index):
        return Response("Variables connues : %s." %
                        ", ".join(context.data.getNode("variables").index.keys()),
                        channel=msg.channel)
    else:
        return Response("No variable are currently stored.", channel=msg.channel)


@hook("cmd_hook", "alias")
def cmd_alias(msg):
    if len(msg.args):
        res = list()
        for alias in msg.args:
            if alias[0] == "!":
                alias = alias[1:]
            if alias in context.data.getNode("aliases").index:
                res.append("!%s correspond à %s" % (alias, context.data.getNode("aliases").index[alias]["origin"]))
            else:
                res.append("!%s n'est pas un alias" % alias)
        return Response(res, channel=msg.channel, nick=msg.nick)
    else:
        return Response("!alias prend en argument l'alias à étendre.",
                        channel=msg.channel, nick=msg.nick)


@hook("cmd_hook", "unalias")
def cmd_unalias(msg):
    if len(msg.args):
        res = list()
        for alias in msg.args:
            if alias[0] == "!" and len(alias) > 1:
                alias = alias[1:]
            if alias in context.data.getNode("aliases").index:
                context.data.getNode("aliases").delChild(context.data.getNode("aliases").index[alias])
                res.append(Response("%s a bien été supprimé" % alias,
                                    channel=msg.channel))
            else:
                res.append(Response("%s n'est pas un alias" % alias,
                                    channel=msg.channel))
        return res
    else:
        return Response("!unalias prend en argument l'alias à supprimer.",
                        channel=msg.channel)


def replace_variables(cnt, msg=None):
    if isinstance(cnt, list):
        return [replace_variables(c, msg) for c in cnt]

    unsetCnt = list()
    for res in re.findall("\\$\{(?P<name>[a-zA-Z0-9:]+)\}", cnt):
        rv = re.match("([0-9]+)(:([0-9]*))?", res)
        if rv is not None:
            varI = int(rv.group(1)) - 1
            print(varI, len(msg.args))
            if varI > len(msg.args):
                cnt = cnt.replace("${%s}" % res, "", 1)
            elif rv.group(2) is not None:
                if rv.group(3) is not None:
                    varJ = int(rv.group(3)) - 1
                    cnt = cnt.replace("${%s}" % res, " ".join(msg.args[varI:varJ]), 1)
                else:
                    cnt = cnt.replace("${%s}" % res, " ".join(msg.args[varI:]), 1)
            else:
                cnt = cnt.replace("${%s}" % res, msg.args[varI], 1)
            unsetCnt.append(varI)
        else:
            cnt = cnt.replace("${%s}" % res, get_variable(res), 1)
    for u in sorted(unsetCnt, reverse=True):
        msg.args.pop(u)
    return cnt


@hook("pre_Command")
def treat_alias(msg):
    if msg.cmd in context.data.getNode("aliases").index:
        txt = context.data.getNode("aliases").index[msg.cmd]["origin"]
        # TODO: for legacy compatibility
        if txt[0] == "!":
            txt = txt[1:]
        try:
            args = shlex.split(txt)
        except ValueError:
            args = txt.split(' ')
        nmsg = Command(args[0], replace_variables(args[1:], msg) + msg.args, **msg.export_args())

        # Avoid infinite recursion
        if msg.cmd != nmsg.cmd:
            # Also return origin message, if it can be treated as well
            return [msg, nmsg]

    return msg


@hook("ask_default")
def parseask(msg):
    if re.match(".*(set|cr[ée]{2}|nouvel(le)?) alias.*", msg.text) is not None:
        result = re.match(".*alias !?([^ ]+) (pour|=|:) (.+)$", msg.text)
        if result.group(1) in context.data.getNode("aliases").index:
            raise IRCException("cet alias est déjà défini.")
        else:
            alias = ModuleState("alias")
            alias["alias"] = result.group(1)
            alias["origin"] = result.group(3)
            alias["creator"] = msg.nick
            context.data.getNode("aliases").addChild(alias)
            res = Response("Nouvel alias %s défini avec succès." %
                           result.group(1), channel=msg.channel)
            context.save()
            return res
    return None
