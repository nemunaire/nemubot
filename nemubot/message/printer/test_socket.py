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

import unittest

from nemubot.message import Command, DirectAsk, Text
from nemubot.message.printer.socket import Socket as SocketVisitor

class TestSocketPrinter(unittest.TestCase):


    def setUp(self):
        self.msgs = [
            # Texts
            (
                Text(message="TEXT",
                ),
                "TEXT"
            ),
            (
                Text(message="TEXT TEXT2",
                ),
                "TEXT TEXT2"
            ),
            (
                Text(message="TEXT @ARG=1 TEXT2",
                ),
                "TEXT @ARG=1 TEXT2"
            ),


            # DirectAsk
            (
                DirectAsk(message="TEXT",
                          designated="someone",
                          to=["#somechannel"]
                ),
                "someone: TEXT"
            ),
            (
                # Private message to someone
                DirectAsk(message="TEXT",
                          designated="someone",
                          to=["someone"]
                ),
                "TEXT"
            ),


            # Commands
            (
                Command(cmd="COMMAND",
                ),
                "!COMMAND"
            ),
            (
                Command(cmd="COMMAND",
                        args=["TEXT"],
                ),
                "!COMMAND TEXT"
            ),
            (
                Command(cmd="COMMAND",
                        kwargs={"KEY1": "VALUE"},
                ),
                "!COMMAND @KEY1=VALUE"
            ),
            (
                Command(cmd="COMMAND",
                        args=["TEXT"],
                        kwargs={"KEY1": "VALUE"},
                ),
                "!COMMAND @KEY1=VALUE TEXT"
            ),
            (
                Command(cmd="COMMAND",
                        kwargs={"KEY2": None},
                ),
                "!COMMAND @KEY2"
            ),
            (
                Command(cmd="COMMAND",
                        args=["TEXT"],
                        kwargs={"KEY2": None},
                ),
                "!COMMAND @KEY2 TEXT"
            ),
        ]


    def test_printer(self):
        for msg, pp in self.msgs:
            sv = SocketVisitor()
            msg.accept(sv)
            self.assertEqual(sv.pp, pp)


if __name__ == '__main__':
    unittest.main()
