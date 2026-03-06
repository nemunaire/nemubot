# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2026  Mercier Pierre-Olivier
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
import os
import queue

from nemubot.bot import sync_act


class ThreadedServer:

    """A server backed by a library running in its own thread.

    Uses an os.pipe() as a fake file descriptor to integrate with the bot's
    select.poll() main loop without requiring direct socket access.

    When the library thread has a message ready, it calls _push_message(),
    which writes a wakeup byte to the pipe's write end. The bot's poll loop
    sees the read end become readable, calls async_read(), which drains the
    message queue and yields already-parsed bot-level messages.

    This abstraction lets any IM library (IRC via python-irc, Matrix via
    matrix-nio, …) plug into nemubot without touching bot.py.
    """

    def __init__(self, name):
        self._name = name
        self._logger = logging.getLogger("nemubot.server." + name)
        self._queue = queue.Queue()
        self._pipe_r, self._pipe_w = os.pipe()


    @property
    def name(self):
        return self._name

    def fileno(self):
        return self._pipe_r


    # Open/close

    def connect(self):
        """Start the library and register the pipe read-end with the poll loop."""
        self._logger.info("Starting connection")
        self._start()
        sync_act("sckt", "register", self._pipe_r)

    def _start(self):
        """Override: start the library's connection (e.g. launch a thread)."""
        raise NotImplementedError

    def close(self):
        """Unregister from poll, stop the library, and close the pipe."""
        self._logger.info("Closing connection")
        sync_act("sckt", "unregister", self._pipe_r)
        self._stop()
        for fd in (self._pipe_w, self._pipe_r):
            try:
                os.close(fd)
            except OSError:
                pass

    def _stop(self):
        """Override: stop the library thread gracefully."""
        pass


    # Writes

    def send_response(self, response):
        """Override: send a response via the underlying library."""
        raise NotImplementedError

    def async_write(self):
        """No-op: writes go directly through the library, not via poll."""
        pass


    # Read

    def _push_message(self, msg):
        """Called from the library thread to enqueue a bot-level message.

        Writes a wakeup byte to the pipe so the main loop wakes up and
        calls async_read().
        """
        self._queue.put(msg)
        try:
            os.write(self._pipe_w, b'\x00')
        except OSError:
            pass  # pipe closed during shutdown

    def async_read(self):
        """Called by the bot when the pipe is readable.

        Drains the wakeup bytes and yields all queued bot messages.
        """
        try:
            os.read(self._pipe_r, 256)
        except OSError:
            return
        while not self._queue.empty():
            try:
                yield self._queue.get_nowait()
            except queue.Empty:
                break

    def parse(self, msg):
        """Messages pushed via _push_message are already bot-level — pass through."""
        yield msg


    # Exceptions

    def exception(self, flags):
        """Called by the bot on POLLERR/POLLHUP/POLLNVAL."""
        self._logger.warning("Exception on server %s: flags=0x%x", self._name, flags)
