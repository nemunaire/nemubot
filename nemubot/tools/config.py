# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2015  Mercier Pierre-Olivier
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

def get_boolean(s):
    if isinstance(s, bool):
        return s
    else:
        return (s and s != "0" and s.lower() != "false" and s.lower() != "off")


class GenericNode:

    def __init__(self, tag, **kwargs):
        self.tag = tag
        self.attrs = kwargs
        self.content = ""
        self.children = []
        self._cur = None
        self._deep_cur = 0


    def startElement(self, name, attrs):
        if self._cur is None:
            self._cur = GenericNode(name, **attrs)
            self._deep_cur = 0
        else:
            self._deep_cur += 1
            self._cur.startElement(name, attrs)
        return True


    def characters(self, content):
        if self._cur is None:
            self.content += content
        else:
            self._cur.characters(content)


    def endElement(self, name):
        if name is None:
            return

        if self._deep_cur:
            self._deep_cur -= 1
            self._cur.endElement(name)
        else:
            self.children.append(self._cur)
            self._cur = None
        return True


    def hasNode(self, nodename):
        return self.getNode(nodename) is not None


    def getNode(self, nodename):
        for c in self.children:
            if c is not None and c.tag == nodename:
                return c
        return None


    def __getitem__(self, item):
        return self.attrs[item]

    def __contains__(self, item):
        return item in self.attrs


class NemubotConfig:

    def __init__(self, nick="nemubot", realname="nemubot", owner=None,
                 ip=None, ssl=False, caps=None, encoding="utf-8"):
        self.nick = nick
        self.realname = realname
        self.owner = owner
        self.ip = ip
        self.caps = caps.split(" ") if caps is not None else []
        self.encoding = encoding
        self.servers = []
        self.modules = []
        self.includes = []


    def addChild(self, name, child):
        if name == "module" and isinstance(child, ModuleConfig):
            self.modules.append(child)
            return True
        elif name == "server" and isinstance(child, ServerConfig):
            self.servers.append(child)
            return True
        elif name == "include" and isinstance(child, IncludeConfig):
            self.includes.append(child)
            return True


class ServerConfig:

    def __init__(self, uri="irc://nemubot@localhost/", autoconnect=True, caps=None, **kwargs):
        self.uri = uri
        self.autoconnect = autoconnect
        self.caps = caps.split(" ") if caps is not None else []
        self.args = kwargs
        self.channels = []


    def addChild(self, name, child):
        if name == "channel" and isinstance(child, Channel):
            self.channels.append(child)
            return True


    def server(self, parent):
        from nemubot.server import factory

        for a in ["nick", "owner", "realname", "encoding"]:
            if a not in self.args:
                self.args[a] = getattr(parent, a)

        self.caps += parent.caps

        return factory(self.uri, **self.args)


class IncludeConfig:

    def __init__(self, path):
        self.path = path


class ModuleConfig(GenericNode):

    def __init__(self, name, autoload=True, **kwargs):
        super(ModuleConfig, self).__init__(None, **kwargs)
        self.name = name
        self.autoload = get_boolean(autoload)

from nemubot.channel import Channel

config_nodes = {
    "nemubotconfig": NemubotConfig,
    "server": ServerConfig,
    "channel": Channel,
    "module": ModuleConfig,
    "include": IncludeConfig,
}
