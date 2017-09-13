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

import logging
import queue

from nemubot.bot import sync_act


class AbstractServer:

    """An abstract server: handle communication with an IM server"""

    def __init__(self, name=None, **kwargs):
        """Initialize an abstract server

        Keyword argument:
        name -- Identifier of the socket, for convinience
        """

        self._name = name
        self._socket = socket

        super().__init__(**kwargs)

        self._logger = logging.getLogger("nemubot.server." + str(self.name))
        self._readbuffer = b''
        self._sending_queue = queue.Queue()


    @property
    def name(self):
        if self._name is not None:
            return self._name
        else:
            return self.fileno()


    # Open/close

    def connect(self, *args, **kwargs):
        """Register the server in _poll"""

        self._logger.info("Opening connection")

        super().connect(*args, **kwargs)

        self._on_connect()

    def _on_connect(self):
        sync_act("sckt", "register", self.fileno())


    def close(self, *args, **kwargs):
        """Unregister the server from _poll"""

        self._logger.info("Closing connection")

        if self.fileno() > 0:
            sync_act("sckt", "unregister", self.fileno())

        super().close(*args, **kwargs)


    # Writes

    def write(self, message):
        """Asynchronymously send a message to the server using send_callback

        Argument:
        message -- message to send
        """

        self._sending_queue.put(self.format(message))
        self._logger.debug("Message '%s' appended to write queue", message)
        sync_act("sckt", "write", self.fileno())


    def async_write(self):
        """Internal function used when the file descriptor is writable"""

        try:
            sync_act("sckt", "unwrite", self.fileno())
            while not self._sending_queue.empty():
                self._write(self._sending_queue.get_nowait())
                self._sending_queue.task_done()

        except queue.Empty:
            pass


    def send_response(self, response):
        """Send a formated Message class

        Argument:
        response -- message to send
        """

        if response is None:
            return

        elif isinstance(response, list):
            for r in response:
                self.send_response(r)

        else:
            vprnt = self.printer()
            response.accept(vprnt)
            self.write(vprnt.pp)


    # Read

    def async_read(self):
        """Internal function used when the file descriptor is readable

        Returns:
        A list of fully received messages
        """

        ret, self._readbuffer = self.lex(self._readbuffer + self.read())

        for r in ret:
            yield r


    def lex(self, buf):
        """Assume lexing in default case is per line

        Argument:
        buf -- buffer to lex
        """

        msgs = buf.split(b'\r\n')
        partial = msgs.pop()

        return msgs, partial


    def parse(self, msg):
        raise NotImplemented


    # Exceptions

    def exception(self, flags):
        """Exception occurs on fd"""

        self.close()
