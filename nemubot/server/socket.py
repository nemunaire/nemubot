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

import os
import socket
import ssl

import nemubot.message as message
from nemubot.message.printer.socket import Socket as SocketPrinter
from nemubot.server.abstract import AbstractServer


class _Socket(AbstractServer):

    """Concrete implementation of a socket connection"""

    def __init__(self, printer=SocketPrinter, **kwargs):
        """Create a server socket
        """

        super().__init__(**kwargs)

        self.readbuffer = b''
        self.printer  = printer


    # Write

    def _write(self, cnt):
        self.sendall(cnt)


    def format(self, txt):
        if isinstance(txt, bytes):
            return txt + b'\r\n'
        else:
            return txt.encode() + b'\r\n'


    # Read

    def recv(self, n=1024):
        return super().recv(n)


    def parse(self, line):
        """Implement a default behaviour for socket"""
        import shlex

        line = line.strip().decode()
        try:
            args = shlex.split(line)
        except ValueError:
            args = line.split(' ')

        if len(args):
            yield message.Command(cmd=args[0], args=args[1:], server=self.fileno(), to=["you"], frm="you")


    def subparse(self, orig, cnt):
        for m in self.parse(cnt):
            m.to = orig.to
            m.frm = orig.frm
            m.date = orig.date
            yield m


class _SocketServer(_Socket):

    def __init__(self, host, port, bind=None, **kwargs):
        super().__init__(family=socket.AF_INET, **kwargs)

        assert(host is not None)
        assert(isinstance(port, int))

        self._host = host
        self._port = port
        self._bind = bind


    @property
    def host(self):
        return self._host


    def connect(self):
        self.logger.info("Connection to %s:%d", self._host, self._port)
        super().connect((self._host, self._port))

        if self._bind:
            super().bind(self._bind)


class SocketServer(_SocketServer, socket.socket):
    pass


class SecureSocketServer(_SocketServer, ssl.SSLSocket):
    pass


class UnixSocket:

    def __init__(self, location, **kwargs):
        super().__init__(family=socket.AF_UNIX, **kwargs)

        self._socket_path = location


    def connect(self):
        self.logger.info("Connection to unix://%s", self._socket_path)
        super().connect(self._socket_path)


class _Listener:

    def __init__(self, new_server_cb, instanciate=_Socket, **kwargs):
        super().__init__(**kwargs)

        self._instanciate = instanciate
        self._new_server_cb = new_server_cb


    def read(self):
        conn, addr = self.accept()
        fileno = conn.fileno()
        self.logger.info("Accept new connection from %s (fd=%d)", addr, fileno)

        ss = self._instanciate(name=self.name + "#" + str(fileno), fileno=conn.detach())
        ss.connect = ss._on_connect
        self._new_server_cb(ss, autoconnect=True)

        return b''


class UnixSocketListener(_Listener, UnixSocket, _Socket, socket.socket):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def connect(self):
        self.logger.info("Creating Unix socket at unix://%s", self._socket_path)

        try:
            os.remove(self._socket_path)
        except FileNotFoundError:
            pass

        self.bind(self._socket_path)
        self.listen(5)
        self.logger.info("Socket ready for accepting new connections")

        self._on_connect()


    def close(self):
        import os
        import socket

        try:
            self.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass

        super().close()

        try:
            if self._socket_path is not None:
                os.remove(self._socket_path)
        except:
            pass
