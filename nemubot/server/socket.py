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
        self._fd.sendall(cnt)


    def format(self, txt):
        if isinstance(txt, bytes):
            return txt + b'\r\n'
        else:
            return txt.encode() + b'\r\n'


    # Read

    def recv(self, *args, **kwargs):
        return self._fd.recv(*args, **kwargs)


    def parse(self, line):
        """Implement a default behaviour for socket"""
        import shlex

        line = line.strip().decode()
        try:
            args = shlex.split(line)
        except ValueError:
            args = line.split(' ')

        if len(args):
            yield message.Command(cmd=args[0], args=args[1:], server=self._fd.fileno(), to=["you"], frm="you")


    def subparse(self, orig, cnt):
        for m in self.parse(cnt):
            m.to = orig.to
            m.frm = orig.frm
            m.date = orig.date
            yield m


class SocketServer(_Socket):

    def __init__(self, host, port, bind=None, **kwargs):
        (family, type, proto, canonname, self._sockaddr) = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)[0]

        super().__init__(fdClass=socket.socket, family=family, type=type, proto=proto, **kwargs)

        self._bind = bind


    def connect(self):
        self._logger.info("Connecting to %s:%d", *self._sockaddr[:2])
        super().connect(self._sockaddr)
        self._logger.info("Connected to %s:%d", *self._sockaddr[:2])

        if self._bind:
            self._fd.bind(self._bind)


class UnixSocket:

    def __init__(self, location, **kwargs):
        super().__init__(fdClass=socket.socket, family=socket.AF_UNIX, **kwargs)

        self._socket_path = location


    def connect(self):
        self._logger.info("Connection to unix://%s", self._socket_path)
        self.connect(self._socket_path)


class SocketClient(_Socket):

    def __init__(self, **kwargs):
        super().__init__(fdClass=socket.socket, **kwargs)


    def read(self):
        return self._fd.recv()


class _Listener:

    def __init__(self, new_server_cb, instanciate=SocketClient, **kwargs):
        super().__init__(**kwargs)

        self._instanciate = instanciate
        self._new_server_cb = new_server_cb


    def read(self):
        conn, addr = self._fd.accept()
        fileno = conn.fileno()
        self._logger.info("Accept new connection from %s (fd=%d)", addr, fileno)

        ss = self._instanciate(name=self.name + "#" + str(fileno), fileno=conn.detach())
        ss.connect = ss._on_connect
        self._new_server_cb(ss, autoconnect=True)

        return b''


class UnixSocketListener(_Listener, UnixSocket, _Socket):

    def connect(self):
        self._logger.info("Creating Unix socket at unix://%s", self._socket_path)

        try:
            os.remove(self._socket_path)
        except FileNotFoundError:
            pass

        self._fd.bind(self._socket_path)
        self._fd.listen(5)
        self._logger.info("Socket ready for accepting new connections")

        self._on_connect()


    def close(self):
        import os
        import socket

        try:
            self._fd.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass

        super().close()

        try:
            if self._socket_path is not None:
                os.remove(self._socket_path)
        except:
            pass
