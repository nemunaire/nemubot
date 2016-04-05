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

from nemubot.datastore.nodes import Serializable


class Scope(Serializable):


    serializetag = "nemubot-scope"
    default_limit = "channel"


    def __init__(self, server, channel, nick, limit=default_limit):
        self._server = server
        self._channel = channel
        self._nick = nick
        self._limit = limit


    def sameServer(self, server):
        return self._server is None or self._server == server


    def sameChannel(self, server, channel):
        return self.sameServer(server) and (self._channel is None or self._channel == channel)


    def sameNick(self, server, channel, nick):
        return self.sameChannel(server, channel) and (self._nick is None or self._nick == nick)


    def check(self, scope, limit=None):
        return self.checkScope(scope._server, scope._channel, scope._nick, limit)


    def checkScope(self, server, channel, nick, limit=None):
        if limit is None: limit = self._limit
        assert limit == "global" or limit == "server" or limit == "channel" or limit == "nick"

        if limit == "server":
            return self.sameServer(server)
        elif limit == "channel":
            return self.sameChannel(server, channel)
        elif limit == "nick":
            return self.sameNick(server, channel, nick)
        else:
            return True


    def narrow(self, scope):
        return scope is None or (
            scope._limit == "global" or
            (scope._limit == "server" and (self._limit == "nick" or self._limit == "channel")) or
            (scope._limit == "channel" and self._limit == "nick")
        )


    def serialize(self):
        from nemubot.datastore.nodes import ParsingNode
        args = {}
        if self._server is not None:
            args["server"] = self._server
        if self._channel is not None:
            args["channel"] = self._channel
        if self._nick is not None:
            args["nick"] = self._nick
        if self._limit is not None:
            args["limit"] = self._limit
        return ParsingNode(tag=self.serializetag, **args)
