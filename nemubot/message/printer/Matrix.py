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


class Matrix(AbstractVisitor):

    """Visitor that sends bot responses as Matrix room messages.

    Instead of accumulating text like the IRC printer does, each visit_*
    method calls send_func(room_id, text) directly for every destination room.
    """

    def __init__(self, send_func):
        """
        Argument:
        send_func -- callable(room_id: str, text: str) that sends a plain-text
                     message to the given Matrix room
        """
        self._send = send_func

    def visit_Text(self, msg):
        if isinstance(msg.message, str):
            for room in msg.to:
                self._send(room, msg.message)
        else:
            # Nested message object — let it visit itself
            msg.message.accept(self)

    def visit_DirectAsk(self, msg):
        text = msg.message if isinstance(msg.message, str) else str(msg.message)
        # Rooms that are NOT the designated nick → prefix with "nick: "
        others = [to for to in msg.to if to != msg.designated]
        if len(others) == 0 or len(others) != len(msg.to):
            # At least one room IS the designated target → send plain
            for room in msg.to:
                self._send(room, text)
        if len(others):
            # Other rooms → prefix with nick
            for room in others:
                self._send(room, "%s: %s" % (msg.designated, text))

    def visit_Command(self, msg):
        parts = ["!" + msg.cmd]
        if msg.args:
            parts.extend(msg.args)
        for room in msg.to:
            self._send(room, " ".join(parts))

    def visit_OwnerCommand(self, msg):
        parts = ["`" + msg.cmd]
        if msg.args:
            parts.extend(msg.args)
        for room in msg.to:
            self._send(room, " ".join(parts))
