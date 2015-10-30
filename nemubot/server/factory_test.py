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

from nemubot.server import factory

class TestFactory(unittest.TestCase):

    def test_IRC1(self):
        from nemubot.server.IRC import IRC as IRCServer

        # <host>: If omitted, the client must connect to a prespecified default IRC server.
        server = factory("irc:///")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server.host, "localhost")
        self.assertFalse(server.ssl)

        server = factory("ircs:///")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server.host, "localhost")
        self.assertTrue(server.ssl)

        server = factory("irc://host1")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server.host, "host1")
        self.assertFalse(server.ssl)

        server = factory("irc://host2:6667")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server.host, "host2")
        self.assertEqual(server.port, 6667)
        self.assertFalse(server.ssl)

        server = factory("ircs://host3:194/")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server.host, "host3")
        self.assertEqual(server.port, 194)
        self.assertTrue(server.ssl)


if __name__ == '__main__':
    unittest.main()
