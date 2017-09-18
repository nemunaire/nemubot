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
        import socket
        import ssl

        # <host>: If omitted, the client must connect to a prespecified default IRC server.
        server = factory("irc:///")
        self.assertIsInstance(server, IRCServer)
        self.assertIsInstance(server._fd, socket.socket)
        self.assertIn(server._sockaddr[0], ["127.0.0.1", "::1"])

        server = factory("irc://2.2.2.2")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server._sockaddr[0], "2.2.2.2")

        server = factory("ircs://1.2.1.2")
        self.assertIsInstance(server, IRCServer)
        self.assertIsInstance(server._fd, ssl.SSLSocket)

        server = factory("irc://1.2.3.4:6667")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server._sockaddr[0], "1.2.3.4")
        self.assertEqual(server._sockaddr[1], 6667)

        server = factory("ircs://4.3.2.1:194/")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server._sockaddr[0], "4.3.2.1")
        self.assertEqual(server._sockaddr[1], 194)


if __name__ == '__main__':
    unittest.main()
