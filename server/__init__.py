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

import io
import imp
import logging
import socket
import queue

# Lists for select
_rlist = []
_wlist = []
_xlist = []

# Extends from IOBase in order to be compatible with select function
class AbstractServer(io.IOBase):

    """An abstract server: handle communication with an IM server"""

    def __init__(self, send_callback=None):
        """Initialize an abstract server

        Keyword argument:
        send_callback -- Callback when developper want to send a message
        """

        if not hasattr(self, "id"):
            raise Exception("No id defined for this server. Please set one!")

        self.logger = logging.getLogger("nemubot.server." + self.id)
        self._sending_queue = queue.Queue()
        if send_callback is not None:
            self._send_callback = send_callback
        else:
            self._send_callback = self._write_select


    # Open/close

    def __enter__(self):
        self.open()
        return self


    def __exit__(self, type, value, traceback):
        self.close()


    def open(self):
        """Generic open function that register the server un _rlist in case of successful _open"""
        self.logger.info("Opening connection to %s", self.id)
        if self._open():
            _rlist.append(self)
            _xlist.append(self)


    def close(self):
        """Generic close function that register the server un _{r,w,x}list in case of successful _close"""
        self.logger.info("Closing connection to %s", self.id)
        if self._close():
            if self in _rlist:
                _rlist.remove(self)
            if self in _wlist:
                _wlist.remove(self)
            if self in _xlist:
                _xlist.remove(self)


    # Writes

    def write(self, message):
        """Asynchronymously send a message to the server using send_callback

        Argument:
        message -- message to send
        """

        self._send_callback(message)


    def write_select(self):
        """Internal function used by the select function"""
        try:
            _wlist.remove(self)
            while not self._sending_queue.empty():
                self._write(self._sending_queue.get_nowait())
                self._sending_queue.task_done()

        except queue.Empty:
            pass


    def _write_select(self, message):
        """Send a message to the server safely through select

        Argument:
        message -- message to send
        """

        self._sending_queue.put(self.format(message))
        self.logger.debug("Message '%s' appended to Queue", message)
        if self not in _wlist:
            _wlist.append(self)


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


    # Exceptions

    def exception(self):
        """Exception occurs in fd"""
        self.logger.warning("Unhandle file descriptor exception on server %s",
                            self.id)


def reload():
    import server.socket
    imp.reload(server.socket)

    import server.IRC
    imp.reload(server.IRC)
