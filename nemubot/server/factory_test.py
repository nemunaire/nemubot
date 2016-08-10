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

import socket
import unittest

from nemubot.server import factory

class TestFactory(unittest.TestCase):

    def test_IRC1(self):
        from nemubot.server.IRC import IRC as IRCServer
        from nemubot.server.IRC import IRC_secure as IRCSServer

        # <host>: If omitted, the client must connect to a prespecified default IRC server.
        server = factory("irc:///")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server._sockaddr,
                         socket.getaddrinfo("localhost", 6667, proto=socket.IPPROTO_TCP)[0][4])

        server = factory("ircs:///")
        self.assertIsInstance(server, IRCSServer)
        self.assertEqual(server._sockaddr,
                         socket.getaddrinfo("localhost", 6667, proto=socket.IPPROTO_TCP)[0][4])

        server = factory("irc://freenode.net")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server._sockaddr,
                         socket.getaddrinfo("freenode.net", 6667, proto=socket.IPPROTO_TCP)[0][4])

        server = factory("irc://freenode.org:1234")
        self.assertIsInstance(server, IRCServer)
        self.assertEqual(server._sockaddr,
                         socket.getaddrinfo("freenode.org", 1234, proto=socket.IPPROTO_TCP)[0][4])

        server = factory("ircs://nemunai.re:194/")
        self.assertIsInstance(server, IRCSServer)
        self.assertEqual(server._sockaddr,
                         socket.getaddrinfo("nemunai.re", 194, proto=socket.IPPROTO_TCP)[0][4])

        with self.assertRaises(socket.gaierror):
            factory("irc://_nonexistent.nemunai.re")


if __name__ == '__main__':
    unittest.main()
