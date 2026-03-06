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

import asyncio
import shlex
import threading

import nemubot.message as message
from nemubot.server.threaded import ThreadedServer


class Matrix(ThreadedServer):

    """Matrix server implementation using matrix-nio's AsyncClient.

    Runs an asyncio event loop in a daemon thread.  Incoming room messages are
    converted to nemubot bot messages and pushed through the pipe; outgoing
    responses are sent via the async client from the same event loop.
    """

    def __init__(self, homeserver, user_id, password=None, access_token=None,
                 owner=None, nick=None, channels=None, **kwargs):
        """Prepare a connection to a Matrix homeserver.

        Keyword arguments:
        homeserver   -- base URL of the homeserver, e.g. "https://matrix.org"
        user_id      -- full MXID (@user:server) or bare localpart
        password     -- login password (required if no access_token)
        access_token -- pre-obtained access token (alternative to password)
        owner        -- MXID of the bot owner (marks frm_owner on messages)
        nick         -- display name / prefix for DirectAsk detection
        channels     -- list of room IDs / aliases to join on connect
        """

        # Ensure fully-qualified MXID
        if not user_id.startswith("@"):
            host = homeserver.split("//")[-1].rstrip("/")
            user_id = "@%s:%s" % (user_id, host)

        super().__init__(name=user_id)

        self.homeserver = homeserver
        self.user_id = user_id
        self.password = password
        self.access_token = access_token
        self.owner = owner
        self.nick = nick or user_id

        self._initial_rooms = channels or []
        self._client = None
        self._loop = None
        self._thread = None


    # Open/close

    def _start(self):
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="nemubot.Matrix/" + self._name,
        )
        self._thread.start()

    def _stop(self):
        if self._client and self._loop and not self._loop.is_closed():
            try:
                asyncio.run_coroutine_threadsafe(
                    self._client.close(), self._loop
                ).result(timeout=5)
            except Exception:
                self._logger.exception("Error while closing Matrix client")
        if self._thread:
            self._thread.join(timeout=5)


    # Asyncio thread

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._async_main())
        except Exception:
            self._logger.exception("Unhandled exception in Matrix event loop")
        finally:
            self._loop.close()

    async def _async_main(self):
        from nio import AsyncClient, LoginError, RoomMessageText

        self._client = AsyncClient(self.homeserver, self.user_id)

        if self.access_token:
            self._client.access_token = self.access_token
            self._logger.info("Using provided access token for %s", self.user_id)
        elif self.password:
            resp = await self._client.login(self.password)
            if isinstance(resp, LoginError):
                self._logger.error("Matrix login failed: %s", resp.message)
                return
            self._logger.info("Logged in to Matrix as %s", self.user_id)
        else:
            self._logger.error("Need either password or access_token to connect")
            return

        self._client.add_event_callback(self._on_room_message, RoomMessageText)

        for room in self._initial_rooms:
            await self._client.join(room)
            self._logger.info("Joined room %s", room)

        await self._client.sync_forever(timeout=30000, full_state=True)


    # Incoming messages

    async def _on_room_message(self, room, event):
        """Callback invoked by matrix-nio for each m.room.message event."""

        if event.sender == self.user_id:
            return  # ignore own messages

        text = event.body
        room_id = room.room_id
        frm = event.sender

        common_args = {
            "server": self.name,
            "to": [room_id],
            "to_response": [room_id],
            "frm": frm,
            "frm_owner": frm == self.owner,
        }

        if len(text) > 1 and text[0] == '!':
            text = text[1:].strip()
            try:
                args = shlex.split(text)
            except ValueError:
                args = text.split(' ')
            msg = message.Command(cmd=args[0], args=args[1:], **common_args)

        elif (text.lower().startswith(self.nick.lower() + ":")
              or text.lower().startswith(self.nick.lower() + ",")):
            text = text[len(self.nick) + 1:].strip()
            msg = message.DirectAsk(designated=self.nick, message=text,
                                    **common_args)

        else:
            msg = message.Text(message=text, **common_args)

        self._push_message(msg)


    # Outgoing messages

    def send_response(self, response):
        if response is None:
            return
        if isinstance(response, list):
            for r in response:
                self.send_response(r)
            return

        from nemubot.message.printer.Matrix import Matrix as MatrixPrinter
        printer = MatrixPrinter(self._send_text)
        response.accept(printer)

    def _send_text(self, room_id, text):
        """Thread-safe: schedule a Matrix room_send on the asyncio loop."""
        if not self._client or not self._loop or self._loop.is_closed():
            self._logger.warning("Cannot send: Matrix client not ready")
            return
        future = asyncio.run_coroutine_threadsafe(
            self._client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": text},
                ignore_unverified_devices=True,
            ),
            self._loop,
        )
        future.add_done_callback(
            lambda f: self._logger.warning("Matrix send error: %s", f.exception())
            if not f.cancelled() and f.exception() else None
        )
