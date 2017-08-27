"""Create alias of commands"""

# PYTHON STUFFS #######################################################

import re
from datetime import datetime, timezone

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.message import Command
from nemubot.tools.human import guess
from nemubot.tools.xmlparser.node import ModuleState

from nemubot.module.more import Response


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
        return None


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


def replace_variables(cnts, msg):
    """Replace variables contained in the content

    Arguments:
    cnt -- content where search variables
    msg -- Message where pick some variables
    """

    unsetCnt = list()
    if not isinstance(cnts, list):
        cnts = list(cnts)
    resultCnt = list()

    for cnt in cnts:
        for res, name, default in re.findall("\\$\{(([a-zA-Z0-9:]+)(?:-([^}]+))?)\}", cnt):
            rv = re.match("([0-9]+)(:([0-9]*))?", name)
            if rv is not None:
                varI = int(rv.group(1)) - 1
                if varI >= len(msg.args):
                    cnt = cnt.replace("${%s}" % res, default, 1)
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
                cnt = cnt.replace("${%s}" % res, get_variable(name) or default, 1)
        resultCnt.append(cnt)

    # Remove used content
    for u in sorted(set(unsetCnt), reverse=True):
        msg.args.pop(u)

    return resultCnt


# MODULE INTERFACE ####################################################

## Variables management

@hook.command("listvars",
      help="list defined variables for substitution in input commands",
      help_usage={
          None: "List all known variables",
          "USER": "List variables created by USER"})
def cmd_listvars(msg):
    if len(msg.args):
        res = list()
        for user in msg.args:
            als = [v["name"] for v in list_variables(user)]
            if len(als) > 0:
                res.append("%s's variables: %s" % (user, ", ".join(als)))
            else:
                res.append("%s didn't create variable yet." % user)
        return Response(" ; ".join(res), channel=msg.channel)
    elif len(context.data.getNode("variables").index):
        return Response(list_variables(),
                        channel=msg.channel,
                        title="Known variables")
    else:
        return Response("There is currently no variable stored.", channel=msg.channel)


@hook.command("set",
      help="Create or set variables for substitution in input commands",
      help_usage={"KEY VALUE": "Define the variable named KEY and fill it with VALUE as content"})
def cmd_set(msg):
    if len(msg.args) < 2:
        raise IMException("!set take two args: the key and the value.")
    set_variable(msg.args[0], " ".join(msg.args[1:]), msg.frm)
    return Response("Variable $%s successfully defined." % msg.args[0],
                    channel=msg.channel)


## Alias management

@hook.command("listalias",
      help="List registered aliases",
      help_usage={
          None: "List all registered aliases",
          "USER": "List all aliases created by USER"})
def cmd_listalias(msg):
    aliases = [a for a in list_alias(None)] + [a for a in list_alias(msg.channel)]
    if len(aliases):
        return Response([a["alias"] for a in aliases],
                        channel=msg.channel,
                        title="Known aliases")
    return Response("There is no alias currently.", channel=msg.channel)


@hook.command("alias",
              help="Display or define the replacement command for a given alias",
              help_usage={
                  "ALIAS": "Extends the given alias",
                  "ALIAS COMMAND [ARGS ...]": "Create a new alias named ALIAS as replacement to the given COMMAND and ARGS",
              })
def cmd_alias(msg):
    if not len(msg.args):
        raise IMException("!alias takes as argument an alias to extend.")

    alias = context.subparse(msg, msg.args[0])
    if alias is None or not isinstance(alias, Command):
        raise IMException("%s is not a valid alias" % msg.args[0])

    if alias.cmd in context.data.getNode("aliases").index:
        return Response("%s corresponds to %s" % (alias.cmd, context.data.getNode("aliases").index[alias.cmd]["origin"]),
                        channel=msg.channel, nick=msg.frm)

    elif len(msg.args) > 1:
        create_alias(alias.cmd,
                     " ".join(msg.args[1:]),
                     channel=msg.channel,
                     creator=msg.frm)
        return Response("New alias %s successfully registered." % alias.cmd,
                        channel=msg.channel)

    else:
        wym = [m for m in guess(alias.cmd, context.data.getNode("aliases").index)]
        raise IMException(msg.args[0] + " is not an alias." + (" Would you mean: %s?" % ", ".join(wym) if len(wym) else ""))


@hook.command("unalias",
      help="Remove a previously created alias")
def cmd_unalias(msg):
    if not len(msg.args):
        raise IMException("Which alias would you want to remove?")
    res = list()
    for alias in msg.args:
        if alias[0] == "!" and len(alias) > 1:
            alias = alias[1:]
        if alias in context.data.getNode("aliases").index:
            context.data.getNode("aliases").delChild(context.data.getNode("aliases").index[alias])
            res.append(Response("%s doesn't exist anymore." % alias,
                                channel=msg.channel))
        else:
            res.append(Response("%s is not an alias" % alias,
                                channel=msg.channel))
    return res


## Alias replacement

@hook.add(["pre","Command"])
def treat_alias(msg):
    if context.data.getNode("aliases") is not None and msg.cmd in context.data.getNode("aliases").index:
        origin = context.data.getNode("aliases").index[msg.cmd]["origin"]
        rpl_msg = context.subparse(msg, origin)
        if isinstance(rpl_msg, Command):
            rpl_msg.args = replace_variables(rpl_msg.args, msg)
            rpl_msg.args += msg.args
            rpl_msg.kwargs.update(msg.kwargs)
        elif len(msg.args) or len(msg.kwargs):
            raise IMException("This kind of alias doesn't take any argument (haven't you forgotten the '!'?).")

        # Avoid infinite recursion
        if not isinstance(rpl_msg, Command) or msg.cmd != rpl_msg.cmd:
            # Also return origin message, if it can be treated as well
            return [msg, rpl_msg]

    return msg
