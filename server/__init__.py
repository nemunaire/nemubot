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

        self.logger = logging.getLogger("nemubot.server.TODO")
        self._sending_queue = queue.Queue()
        if send_callback is not None:
            self._send_callback = send_callback
        else:
            self._send_callback = self._write_select


    def open(self):
        """Generic open function that register the server un _rlist in case of successful _open"""
        if self._open():
            _rlist.append(self)


    def close(self):
        """Generic close function that register the server un _{r,w,x}list in case of successful _close"""
        if self._close():
            if self in _rlist:
                _rlist.remove(self)
            if self in _wlist:
                _wlist.remove(self)
            if self in _xlist:
                _xlist.remove(self)


    def write(self, message):
        """Send a message to the server using send_callback"""
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
        """Send a message to the server safely through select"""
        self._sending_queue.put(self.format(message))
        self.logger.debug("Message '%s' appended to Queue", message)
        if self not in _wlist:
            _wlist.append(self)
