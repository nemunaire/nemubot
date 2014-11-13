# coding=utf-8

"""Create alias of commands"""

import re
import sys
from datetime import datetime, timezone
import shlex

from hooks import hook
from message import TextMessage, Command

nemubotversion = 3.4

from more import Response


def load(context):
    """Load this module"""
    global DATAS
    if not DATAS.hasNode("aliases"):
        DATAS.addChild(ModuleState("aliases"))
    DATAS.getNode("aliases").setIndex("alias")
    if not DATAS.hasNode("variables"):
        DATAS.addChild(ModuleState("variables"))
    DATAS.getNode("variables").setIndex("name")


def help_full():
    return "TODO"


def set_variable(name, value, creator):
    var = ModuleState("variable")
    var["name"] = name
    var["value"] = value
    var["creator"] = creator
    DATAS.getNode("variables").addChild(var)


def get_variable(name, msg=None):
    if name == "sender" or name == "from" or name == "nick":
        return msg.frm
    elif name == "chan" or name == "channel":
        return msg.channel
    elif name == "date":
        return datetime.now(timezone.utc).strftime("%c")
    elif name in DATAS.getNode("variables").index:
        return DATAS.getNode("variables").index[name]["value"]
    else:
        return ""


@hook("cmd_hook", "set")
def cmd_set(msg):
    if len(msg.cmds) > 2:
        set_variable(msg.cmds[1], " ".join(msg.cmds[2:]), msg.nick)
        res = Response("Variable \$%s définie." % msg.cmds[1],
                       channel=msg.channel)
        save()
        return res
    return Response("!set prend au minimum deux arguments : "
                    "le nom de la variable et sa valeur.",
                    channel=msg.channel)


@hook("cmd_hook", "listalias")
def cmd_listalias(msg):
    if len(msg.cmds) > 1:
        res = list()
        for user in msg.cmds[1:]:
            als = [x["alias"] for x in DATAS.getNode("aliases").index.values() if x["creator"] == user]
            if len(als) > 0:
                res.append("Alias créés par %s : %s" % (user, ", ".join(als)))
            else:
                res.append("%s n'a pas encore créé d'alias" % user)
        return Response(" ; ".join(res), channel=msg.channel)
    else:
        return Response("Alias connus : %s." %
                        ", ".join(DATAS.getNode("aliases").index.keys()),
                        channel=msg.channel)


@hook("cmd_hook", "listvars")
def cmd_listvars(msg):
    if len(msg.cmds) > 1:
        res = list()
        for user in msg.cmds[1:]:
            als = [x["alias"] for x in DATAS.getNode("variables").index.values() if x["creator"] == user]
            if len(als) > 0:
                res.append("Variables créées par %s : %s" % (user, ", ".join(als)))
            else:
                res.append("%s n'a pas encore créé de variable" % user)
        return Response(" ; ".join(res), channel=msg.channel)
    else:
        return Response("Variables connues : %s." %
                        ", ".join(DATAS.getNode("variables").index.keys()),
                        channel=msg.channel)


@hook("cmd_hook", "alias")
def cmd_alias(msg):
    if len(msg.cmds) > 1:
        res = list()
        for alias in msg.cmds[1:]:
            if alias[0] == "!":
                alias = alias[1:]
            if alias in DATAS.getNode("aliases").index:
                res.append(Response("!%s correspond à %s" %
                                    (alias, DATAS.getNode("aliases").index[alias]["origin"]),
                                    channel=msg.channel))
            else:
                res.append(Response("!%s n'est pas un alias" % alias,
                                    channel=msg.channel))
        return res
    else:
        return Response("!alias prend en argument l'alias à étendre.",
                        channel=msg.channel)


@hook("cmd_hook", "unalias")
def cmd_unalias(msg):
    if len(msg.cmds) > 1:
        res = list()
        for alias in msg.cmds[1:]:
            if alias[0] == "!" and len(alias) > 1:
                alias = alias[1:]
            if alias in DATAS.getNode("aliases").index:
                if DATAS.getNode("aliases").index[alias]["creator"] == msg.nick or msg.frm_owner:
                    DATAS.getNode("aliases").delChild(DATAS.getNode("aliases").index[alias])
                    res.append(Response("%s a bien été supprimé" % alias,
                                        channel=msg.channel))
                else:
                    res.append(Response("Vous n'êtes pas le createur de "
                                        "l'alias %s." % alias,
                                        channel=msg.channel))
            else:
                res.append(Response("%s n'est pas un alias" % alias,
                                    channel=msg.channel))
        return res
    else:
        return Response("!unalias prend en argument l'alias à supprimer.",
                        channel=msg.channel)


def replace_variables(cnt, msg=None):
    cnt = cnt.split(' ')
    unsetCnt = list()
    for i in range(0, len(cnt)):
        if i not in unsetCnt:
            res = re.match("^([^$]*)(\\\\)?\\$([a-zA-Z0-9]+)(.*)$", cnt[i])
            if res is not None:
                try:
                    varI = int(res.group(3))
                    unsetCnt.append(varI)
                    cnt[i] = res.group(1) + msg.cmds[varI] + res.group(4)
                except:
                    if res.group(2) != "":
                        cnt[i] = res.group(1) + "$" + res.group(3) + res.group(4)
                    else:
                        cnt[i] = (res.group(1) + get_variable(res.group(3), msg) +
                                  res.group(4))
    return " ".join(cnt)


@hook("pre_Command")
def treat_alias(msg):
    if msg.cmd in DATAS.getNode("aliases").index:
        txt = DATAS.getNode("aliases").index[msg.cmd]["origin"]
        # TODO: for legacy compatibility
        if txt[0] == "!":
            txt = txt[1:]
        try:
            args = shlex.split(txt)
        except ValueError:
            args = txt.split(' ')
        nmsg = Command(args[0], args[1:] + msg.args, **msg.export_args())

        # Avoid infinite recursion
        if msg.cmd != nmsg.cmd:
            return nmsg

    return msg


@hook("ask_default")
def parseask(msg):
    global ALIAS
    if re.match(".*(set|cr[ée]{2}|nouvel(le)?) alias.*", msg.text) is not None:
        result = re.match(".*alias !?([^ ]+) (pour|=|:) (.+)$", msg.text)
        if result.group(1) in DATAS.getNode("aliases").index or result.group(3).find("alias") >= 0:
            raise IRCException("cet alias est déjà défini.")
        else:
            alias = ModuleState("alias")
            alias["alias"] = result.group(1)
            alias["origin"] = result.group(3)
            alias["creator"] = msg.nick
            DATAS.getNode("aliases").addChild(alias)
            res = Response("Nouvel alias %s défini avec succès." %
                           result.group(1), channel=msg.channel)
            save()
            return res
    return None
