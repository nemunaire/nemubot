# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2026  Mercier Pierre-Olivier
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

from nemubot.message.visitor import AbstractVisitor


class IRCLib(AbstractVisitor):

    """Visitor that sends bot responses via an irc.client.ServerConnection.

    Unlike the socket-based IRC printer (which builds a raw PRIVMSG string),
    this calls connection.privmsg() directly so the library handles encoding,
    line-length capping, and any internal locking.
    """

    def __init__(self, connection):
        self._conn = connection

    def _send(self, target, text):
        try:
            self._conn.privmsg(target, text)
        except Exception:
            pass  # drop silently during reconnection

    # Visitor methods

    def visit_Text(self, msg):
        if isinstance(msg.message, str):
            for target in msg.to:
                self._send(target, msg.message)
        else:
            msg.message.accept(self)

    def visit_DirectAsk(self, msg):
        text = msg.message if isinstance(msg.message, str) else str(msg.message)
        # Mirrors socket.py logic:
        # rooms that are NOT the designated nick get a "nick: " prefix
        others = [to for to in msg.to if to != msg.designated]
        if len(others) == 0 or len(others) != len(msg.to):
            for target in msg.to:
                self._send(target, text)
        if others:
            for target in others:
                self._send(target, "%s: %s" % (msg.designated, text))

    def visit_Command(self, msg):
        parts = ["!" + msg.cmd] + list(msg.args)
        for target in msg.to:
            self._send(target, " ".join(parts))

    def visit_OwnerCommand(self, msg):
        parts = ["`" + msg.cmd] + list(msg.args)
        for target in msg.to:
            self._send(target, " ".join(parts))
