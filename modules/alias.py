"""Create alias of commands"""

# PYTHON STUFFS #######################################################

import re
import sys
from datetime import datetime, timezone
import shlex

from nemubot import context
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.message import Command
from nemubot.tools.xmlparser.node import ModuleState

from more import Response


# HELP ################################################################

def help_full():
    return "Pour créer un alias, adressez-vous à moi en disant quelque chose comme : \"nouvel alias XX : YY\", où YY sera la commande équivalente à XX. Vous pouvez ajouter des variables comme ${1}, ${2}, ... correspondant aux éventuels arguments.\nDe l'aide supplémentaire existe pour les commandes !alias, !listalias, !unalias, !set et !listvars"

# LOADING #############################################################

def load(context):
    """Load this module"""
    if not context.data.hasNode("aliases"):
        context.data.addChild(ModuleState("aliases"))
    context.data.getNode("aliases").setIndex("alias")
    if not context.data.hasNode("variables"):
        context.data.addChild(ModuleState("variables"))
    context.data.getNode("variables").setIndex("name")


# MODULE CORE #########################################################

## Alias management

def list_alias(channel=None):
    """List known aliases.

    Argument:
    channel -- optional, if defined, return a list of aliases only defined on this channel, else alias widly defined
    """

    for alias in context.data.getNode("aliases").index.values():
        if (channel is None and "channel" not in alias) or (channel is not None and "channel" in alias and alias["channel"] == channel):
            yield alias

def create_alias(alias, origin, channel=None, creator=None):
    """Create or erase an existing alias
    """

    anode = ModuleState("alias")
    anode["alias"] = alias
    anode["origin"] = origin
    if channel is not None:
        anode["creator"] = channel
    if creator is not None:
        anode["creator"] = creator
    context.data.getNode("aliases").addChild(anode)
    context.save()


## Variables management

def get_variable(name, msg=None):
    """Get the value for the given variable

    Arguments:
    name -- The variable identifier
    msg -- optional, original message where some variable can be picked
    """

    if msg is not None and (name == "sender" or name == "from" or name == "nick"):
        return msg.frm
    elif msg is not None and (name == "chan" or name == "channel"):
        return msg.channel
    elif name == "date":
        return datetime.now(timezone.utc).strftime("%c")
    elif name in context.data.getNode("variables").index:
        return context.data.getNode("variables").index[name]["value"]
    else:
        return ""


def list_variables(user=None):
    """List known variables.

    Argument:
    user -- optional, if defined, display only variable created by the given user
    """
    if user is not None:
        return [x for x in context.data.getNode("variables").index.values() if x["creator"] == user]
    else:
        return context.data.getNode("variables").index.values()


def set_variable(name, value, creator):
    """Define or erase a variable.

    Arguments:
    name -- The variable identifier
    value -- Variable value
    creator -- User who has created this variable
    """

    var = ModuleState("variable")
    var["name"] = name
    var["value"] = value
    var["creator"] = creator
    context.data.getNode("variables").addChild(var)
    context.save()


def replace_variables(cnts, msg=None):
    """Replace variables contained in the content

    Arguments:
    cnt -- content where search variables
    msg -- optional message where pick some variables
    """

    unsetCnt = list()
    if not isinstance(cnts, list):
        cnts = list(cnts)
    resultCnt = list()

    for cnt in cnts:
        for res in re.findall("\\$\{(?P<name>[a-zA-Z0-9:]+)\}", cnt):
            rv = re.match("([0-9]+)(:([0-9]*))?", res)
            if rv is not None:
                varI = int(rv.group(1)) - 1
                if varI > len(msg.args):
                    cnt = cnt.replace("${%s}" % res, "", 1)
                elif rv.group(2) is not None:
                    if rv.group(3) is not None and len(rv.group(3)):
                        varJ = int(rv.group(3)) - 1
                        cnt = cnt.replace("${%s}" % res, " ".join(msg.args[varI:varJ]), 1)
                        for v in range(varI, varJ):
                            unsetCnt.append(v)
                    else:
                        cnt = cnt.replace("${%s}" % res, " ".join(msg.args[varI:]), 1)
                        for v in range(varI, len(msg.args)):
                            unsetCnt.append(v)
                else:
                    cnt = cnt.replace("${%s}" % res, msg.args[varI], 1)
                    unsetCnt.append(varI)
            else:
                cnt = cnt.replace("${%s}" % res, get_variable(res), 1)
        resultCnt.append(cnt)

    for u in sorted(set(unsetCnt), reverse=True):
        k = msg.args.pop(u)

    return resultCnt


# MODULE INTERFACE ####################################################

## Variables management

@hook("cmd_hook", "listvars")
def cmd_listvars(msg):
    if len(msg.args):
        res = list()
        for user in msg.args:
            als = [v["alias"] for v in list_variables(user)]
            if len(als) > 0:
                res.append("Variables créées par %s : %s" % (user, ", ".join(als)))
            else:
                res.append("%s n'a pas encore créé de variable" % user)
        return Response(" ; ".join(res), channel=msg.channel)
    elif len(context.data.getNode("variables").index):
        return Response("Variables connues : %s." %
                        ", ".join(list_variables()),
                        channel=msg.channel)
    else:
        return Response("No variable are currently stored.", channel=msg.channel)


@hook("cmd_hook", "set")
def cmd_set(msg):
    if len(msg.args) < 2:
        raise IRCException("!set prend au minimum deux arguments : "
                           "le nom de la variable et sa valeur.")
    set_variable(msg.args[0], " ".join(msg.args[1:]), msg.nick)
    return Response("Variable \$%s définie avec succès." % msg.args[0],
                    channel=msg.channel)


## Alias management

@hook("cmd_hook", "listalias")
def cmd_listalias(msg):
    aliases = [a for a in list_alias(None)] + [a for a in list_alias(msg.channel)]
    if len(aliases):
        return Response([a["alias"] for a in aliases],
                        channel=msg.channel,
                        title="Known aliases:")
    return Response("There is no alias currently.", channel=msg.channel)


@hook("cmd_hook", "alias")
def cmd_alias(msg):
    if not len(msg.args):
        raise IRCException("!alias prend en argument l'alias à étendre.")
    res = list()
    for alias in msg.args:
        if alias[0] == "!":
            alias = alias[1:]
        if alias in context.data.getNode("aliases").index:
            res.append("!%s correspond à %s" % (alias, context.data.getNode("aliases").index[alias]["origin"]))
        else:
            res.append("!%s n'est pas un alias" % alias)
    return Response(res, channel=msg.channel, nick=msg.nick)


@hook("cmd_hook", "unalias")
def cmd_unalias(msg):
    if not len(msg.args):
        raise IRCException("Quel alias voulez-vous supprimer ?")
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


## Alias replacement

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
        result = re.match(".*alias !?([^ ]+) ?(pour|=|:) ?(.+)$", msg.text)
        if result.group(1) in context.data.getNode("aliases").index:
            raise IRCException("cet alias est déjà défini.")
        else:
            create_alias(result.group(1),
                         result.group(3),
                         channel=msg.channel,
                         creator=msg.nick)
            res = Response("Nouvel alias %s défini avec succès." %
                           result.group(1), channel=msg.channel)
            return res
    return None
