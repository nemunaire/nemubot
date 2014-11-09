# -*- coding: utf-8 -*-

# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2014  nemunaire
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

import ssl
import socket

from server import AbstractServer


class SocketServer(AbstractServer):

    """Concrete implementation of a socket connexion (can be wrapped with TLS)"""

    def __init__(self, host, port, ssl=False):
        AbstractServer.__init__(self)
        self.host = host
        self.port = int(port)
        self.ssl = ssl

        self.socket = None
        self.readbuffer = b''


    def fileno(self):
        return self.socket.fileno() if self.socket else None


    @property
    def connected(self):
        """Indicator of the connection aliveness"""
        return self.socket is not None


    # Open/close

    def _open(self):
        # Create the socket
        self.socket = socket.socket()

        # Wrap the socket for SSL
        if self.ssl:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            self.socket = ctx.wrap_socket(self.socket)

        try:
            self.socket.connect((self.host, self.port))  # Connect to server
            self.logger.info("Connected to %s:%d", self.host, self.port)
        except socket.error as e:
            self.socket = None
            self.logger.critical("Unable to connect to %s:%d: %s",
                                 self.host, self.port,
                                 os.strerror(e.errno))
            return False

        return True


    def _close(self):
        self._sending_queue.join()
        if self.connected:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except socket.error:
                pass
            self.socket = None
        return True


    # Write

    def _write(self, cnt):
        if not self.connected:
            return

        self.socket.send(cnt)


    def format(self, txt):
        if isinstance(txt, bytes):
            return txt + b'\r\n'
        else:
            return txt.encode() + b'\r\n'


    # Read

    def read(self):
        if not self.connected:
            return

        raw = self.socket.recv(1024)
        temp = (self.readbuffer + raw).split(b'\r\n')
        self.readbuffer = temp.pop()

        for line in temp:
            yield line
