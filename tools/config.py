# -*- coding: utf-8 -*-

# Nemubot is a modulable IRC bot, built around XML configuration files.
# Copyright (C) 2012  Mercier Pierre-Olivier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import imp
import logging
import os

import xmlparser

logger = logging.getLogger("nemubot.tools.config")


def get_boolean(d, k, default=False):
    return ((k in d and d[k].lower() != "false" and d[k].lower() != "off") or
            (k not in d and default))


def _load_server(config, xmlnode):
    """Load a server configuration

    Arguments:
    config -- the global configuration
    xmlnode -- the current server configuration node
    """

    opts = {
        "host": xmlnode["host"],
        "ssl": xmlnode.hasAttribute("ssl") and xmlnode["ssl"].lower() == "true",

        "nick": xmlnode["nick"] if xmlnode.hasAttribute("nick") else config["nick"],
        "owner": xmlnode["owner"] if xmlnode.hasAttribute("owner") else config["owner"],
    }

    # Optional keyword arguments
    for optional_opt in [ "port", "username", "realname",
                          "password", "encoding", "caps" ]:
        if xmlnode.hasAttribute(optional_opt):
            opts[optional_opt] = xmlnode[optional_opt]
        elif optional_opt in config:
            opts[optional_opt] = config[optional_opt]

    # Command to send on connection
    if "on_connect" in xmlnode:
        def on_connect():
            yield xmlnode["on_connect"]
        opts["on_connect"] = on_connect

    # Channels to autojoin on connection
    if xmlnode.hasNode("channel"):
        opts["channels"] = list()
    for chn in xmlnode.getNodes("channel"):
        opts["channels"].append((chn["name"], chn["password"])
                                if chn["password"] is not None
                                else chn["name"])

    # Server/client capabilities
    if "caps" in xmlnode or "caps" in config:
        capsl = (xmlnode["caps"] if xmlnode.hasAttribute("caps")
                 else config["caps"]).lower()
        if capsl == "no" or capsl == "off" or capsl == "false":
            opts["caps"] = None
        else:
            opts["caps"] = capsl.split(',')
    else:
        opts["caps"] = list()

    # Bind the protocol asked to the corresponding implementation
    if "protocol" not in xmlnode or xmlnode["protocol"] == "irc":
        from server.IRC import IRC as IRCServer
        srvcls = IRCServer
    else:
        raise Exception("Unhandled protocol '%s'" %
                        xmlnode["protocol"])

    # Initialize the server
    return srvcls(**opts)


def load_file(filename, context):
    """Load the configuration file

    Arguments:
    filename -- the path to the file to load
    """

    if os.path.isfile(filename):
        config = xmlparser.parse_file(filename)

        # This is a true nemubot configuration file, load it!
        if config.getName() == "nemubotconfig":
            # Preset each server in this file
            for server in config.getNodes("server"):
                srv = _load_server(config, server)

                # Add the server in the context
                if context.add_server(srv, get_boolean(server, "autoconnect")):
                    print("Server '%s' successfully added." % srv.id)
                else:
                    print("Can't add server '%s'." % srv.id)

            # Load module and their configuration
            for mod in config.getNodes("module"):
                context.modules_configuration[mod["name"]] = mod
                if get_boolean(mod, "autoload", default=True):
                    __import__(mod["name"])

            # Load files asked by the configuration file
            for load in config.getNodes("include"):
                load_file(load["path"], context)

        # Other formats
        else:
            print ("  Can't load `%s'; this is not a valid nemubot "
                   "configuration file." % filename)

    # Unexisting file, assume a name was passed, import the module!
    else:
        tt = __import__(filename)
        imp.reload(tt)
