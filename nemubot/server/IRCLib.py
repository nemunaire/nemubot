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

from datetime import datetime
import shlex
import threading

import irc.bot
import irc.client
import irc.connection

import nemubot.message as message
from nemubot.server.threaded import ThreadedServer


class _IRCBotAdapter(irc.bot.SingleServerIRCBot):

    """Internal adapter that bridges the irc library event model to nemubot.

    Subclasses SingleServerIRCBot to get automatic reconnection, PING/PONG,
    and nick-collision handling for free.
    """

    def __init__(self, server_name, push_fn, channels, on_connect_cmds,
                 nick, server_list, owner=None, realname="Nemubot",
                 encoding="utf-8", **connect_params):
        super().__init__(server_list, nick, realname, **connect_params)
        self._nemubot_name = server_name
        self._push = push_fn
        self._channels_to_join = channels
        self._on_connect_cmds = on_connect_cmds or []
        self.owner = owner
        self.encoding = encoding
        self._stop_event = threading.Event()


    # Event loop control

    def start(self):
        """Run the reactor loop until stop() is called."""
        self._connect()
        while not self._stop_event.is_set():
            self.reactor.process_once(timeout=0.2)

    def stop(self):
        """Signal the loop to exit and disconnect cleanly."""
        self._stop_event.set()
        try:
            self.connection.disconnect("Goodbye")
        except Exception:
            pass

    def on_disconnect(self, connection, event):
        """Reconnect automatically unless we are shutting down."""
        if not self._stop_event.is_set():
            super().on_disconnect(connection, event)


    # Connection lifecycle

    def on_welcome(self, connection, event):
        """001 — run on_connect commands then join channels."""
        for cmd in self._on_connect_cmds:
            if callable(cmd):
                for c in (cmd() or []):
                    connection.send_raw(c)
            else:
                connection.send_raw(cmd)

        for ch in self._channels_to_join:
            if isinstance(ch, tuple):
                connection.join(ch[0], ch[1] if len(ch) > 1 else "")
            elif hasattr(ch, 'name'):
                connection.join(ch.name, getattr(ch, 'password', "") or "")
            else:
                connection.join(str(ch))

    def on_invite(self, connection, event):
        """Auto-join on INVITE."""
        if event.arguments:
            connection.join(event.arguments[0])


    # CTCP

    def on_ctcp(self, connection, event):
        """Handle CTCP requests (irc library >= 19 dispatches all to on_ctcp)."""
        nick = irc.client.NickMask(event.source).nick
        ctcp_type = event.arguments[0].upper() if event.arguments else ""
        ctcp_arg  = event.arguments[1] if len(event.arguments) > 1 else ""
        self._reply_ctcp(connection, nick, ctcp_type, ctcp_arg)

    # Fallbacks for older irc library versions that dispatch per-type
    def on_ctcpversion(self, connection, event):
        import nemubot
        nick = irc.client.NickMask(event.source).nick
        connection.ctcp_reply(nick, "VERSION nemubot v%s" % nemubot.__version__)

    def on_ctcpping(self, connection, event):
        nick = irc.client.NickMask(event.source).nick
        arg = event.arguments[0] if event.arguments else ""
        connection.ctcp_reply(nick, "PING %s" % arg)

    def _reply_ctcp(self, connection, nick, ctcp_type, ctcp_arg):
        import nemubot
        responses = {
            "ACTION":     None,  # handled as on_action
            "CLIENTINFO": "CLIENTINFO ACTION CLIENTINFO FINGER PING SOURCE TIME USERINFO VERSION",
            "FINGER":     "FINGER nemubot v%s" % nemubot.__version__,
            "PING":       "PING %s" % ctcp_arg,
            "SOURCE":     "SOURCE https://github.com/nemunaire/nemubot",
            "TIME":       "TIME %s" % datetime.now(),
            "USERINFO":   "USERINFO Nemubot",
            "VERSION":    "VERSION nemubot v%s" % nemubot.__version__,
        }
        if ctcp_type in responses and responses[ctcp_type] is not None:
            connection.ctcp_reply(nick, responses[ctcp_type])


    # Incoming messages

    def _decode(self, text):
        if isinstance(text, bytes):
            try:
                return text.decode("utf-8")
            except UnicodeDecodeError:
                return text.decode(self.encoding, "replace")
        return text

    def _make_message(self, connection, source, target, text):
        """Convert raw IRC event data into a nemubot bot message."""
        nick = irc.client.NickMask(source).nick
        text = self._decode(text)
        bot_nick = connection.get_nickname()
        is_channel = irc.client.is_channel(target)
        to          = [target] if is_channel else [nick]
        to_response = [target] if is_channel else [nick]

        common = dict(
            server=self._nemubot_name,
            to=to,
            to_response=to_response,
            frm=nick,
            frm_owner=(nick == self.owner),
        )

        # "botname: text" or "botname, text"
        if (text.startswith(bot_nick + ":") or
                text.startswith(bot_nick + ",")):
            inner = text[len(bot_nick) + 1:].strip()
            return message.DirectAsk(designated=bot_nick, message=inner,
                                     **common)

        # "!command [args]"
        if len(text) > 1 and text[0] == '!':
            inner = text[1:].strip()
            try:
                args = shlex.split(inner)
            except ValueError:
                args = inner.split()
            if args:
                # Extract @key=value named arguments (same logic as IRC.py)
                kwargs = {}
                while len(args) > 1:
                    arg = args[1]
                    if len(arg) > 2 and arg[0:2] == '\\@':
                        args[1] = arg[1:]
                    elif len(arg) > 1 and arg[0] == '@':
                        arsp = arg[1:].split("=", 1)
                        kwargs[arsp[0]] = arsp[1] if len(arsp) == 2 else None
                        args.pop(1)
                        continue
                    break
                return message.Command(cmd=args[0], args=args[1:],
                                       kwargs=kwargs, **common)

        return message.Text(message=text, **common)

    def on_pubmsg(self, connection, event):
        msg = self._make_message(
            connection, event.source, event.target,
            event.arguments[0] if event.arguments else "",
        )
        if msg:
            self._push(msg)

    def on_privmsg(self, connection, event):
        nick = irc.client.NickMask(event.source).nick
        msg = self._make_message(
            connection, event.source, nick,
            event.arguments[0] if event.arguments else "",
        )
        if msg:
            self._push(msg)

    def on_action(self, connection, event):
        """CTCP ACTION (/me) — delivered as a plain Text message."""
        nick = irc.client.NickMask(event.source).nick
        text = "/me %s" % (event.arguments[0] if event.arguments else "")
        is_channel = irc.client.is_channel(event.target)
        to = [event.target] if is_channel else [nick]
        self._push(message.Text(
            message=text,
            server=self._nemubot_name,
            to=to, to_response=to,
            frm=nick, frm_owner=(nick == self.owner),
        ))


class IRCLib(ThreadedServer):

    """IRC server using the irc Python library (jaraco).

    Compared to the hand-rolled IRC.py implementation, this gets:
      - Automatic exponential-backoff reconnection
      - PING/PONG handled transparently
      - Nick-collision suffix logic built-in
    """

    def __init__(self, host="localhost", port=6667, nick="nemubot",
                 username=None, password=None, realname="Nemubot",
                 encoding="utf-8", owner=None, channels=None,
                 on_connect=None, ssl=False, **kwargs):
        """Prepare a connection to an IRC server.

        Keyword arguments:
        host       -- IRC server hostname
        port       -- IRC server port (default 6667)
        nick       -- bot's nickname
        username   -- username for USER command (defaults to nick)
        password   -- server password (sent as PASS)
        realname   -- bot's real name
        encoding   -- fallback encoding for non-UTF-8 servers
        owner      -- nick of the bot's owner (sets frm_owner on messages)
        channels   -- list of channel names / (name, key) tuples to join
        on_connect -- list of raw IRC commands (or a callable returning one)
                      to send after receiving 001
        ssl        -- wrap the connection in TLS
        """
        name = (username or nick) + "@" + host + ":" + str(port)
        super().__init__(name=name)

        self._host     = host
        self._port     = int(port)
        self._nick     = nick
        self._username = username or nick
        self._password = password
        self._realname = realname
        self._encoding = encoding
        self.owner     = owner
        self._channels = channels or []
        self._on_connect_cmds = on_connect
        self._ssl      = ssl

        self._bot    = None
        self._thread = None


    # ThreadedServer hooks

    def _start(self):
        server_list = [irc.bot.ServerSpec(self._host, self._port,
                                          self._password)]

        connect_params = {"username": self._username}

        if self._ssl:
            import ssl as ssl_mod
            ctx  = ssl_mod.create_default_context()
            host = self._host  # capture for closure
            connect_params["connect_factory"] = irc.connection.Factory(
                wrapper=lambda sock: ctx.wrap_socket(sock,
                                                     server_hostname=host)
            )

        self._bot = _IRCBotAdapter(
            server_name=self.name,
            push_fn=self._push_message,
            channels=self._channels,
            on_connect_cmds=self._on_connect_cmds,
            nick=self._nick,
            server_list=server_list,
            owner=self.owner,
            realname=self._realname,
            encoding=self._encoding,
            **connect_params,
        )
        self._thread = threading.Thread(
            target=self._bot.start,
            daemon=True,
            name="nemubot.IRC/" + self.name,
        )
        self._thread.start()

    def _stop(self):
        if self._bot:
            self._bot.stop()
        if self._thread:
            self._thread.join(timeout=5)


    # Outgoing messages

    def send_response(self, response):
        if response is None:
            return
        if isinstance(response, list):
            for r in response:
                self.send_response(r)
            return
        if not self._bot:
            return

        from nemubot.message.printer.IRCLib import IRCLib as IRCLibPrinter
        printer = IRCLibPrinter(self._bot.connection)
        response.accept(printer)


    # subparse: re-parse a plain string in the context of an existing message
    # (used by alias, rnd, grep, cat, smmry, sms modules)

    def subparse(self, orig, cnt):
        bot_nick = (self._bot.connection.get_nickname()
                    if self._bot else self._nick)
        common = dict(
            server=self.name,
            to=orig.to,
            to_response=orig.to_response,
            frm=orig.frm,
            frm_owner=orig.frm_owner,
            date=orig.date,
        )
        text = cnt

        if (text.startswith(bot_nick + ":") or
                text.startswith(bot_nick + ",")):
            inner = text[len(bot_nick) + 1:].strip()
            return message.DirectAsk(designated=bot_nick, message=inner,
                                     **common)

        if len(text) > 1 and text[0] == '!':
            inner = text[1:].strip()
            try:
                args = shlex.split(inner)
            except ValueError:
                args = inner.split()
            if args:
                kwargs = {}
                while len(args) > 1:
                    arg = args[1]
                    if len(arg) > 2 and arg[0:2] == '\\@':
                        args[1] = arg[1:]
                    elif len(arg) > 1 and arg[0] == '@':
                        arsp = arg[1:].split("=", 1)
                        kwargs[arsp[0]] = arsp[1] if len(arsp) == 2 else None
                        args.pop(1)
                        continue
                    break
                return message.Command(cmd=args[0], args=args[1:],
                                       kwargs=kwargs, **common)

        return message.Text(message=text, **common)
