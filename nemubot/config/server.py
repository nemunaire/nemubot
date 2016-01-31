# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2016  Mercier Pierre-Olivier
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

from nemubot.channel import Channel


class Server:

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

        return factory(self.uri, caps=self.caps, channels=self.channels, **self.args)
