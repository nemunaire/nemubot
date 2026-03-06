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


def factory(uri, ssl=False, **init_args):
    from urllib.parse import urlparse, unquote, parse_qs
    o = urlparse(uri)

    srv = None

    if o.scheme == "irc" or o.scheme == "ircs":
        # https://www.w3.org/Addressing/draft-mirashi-url-irc-01.txt
        # https://www-archive.mozilla.org/projects/rt-messaging/chatzilla/irc-urls.html
        args = init_args

        if o.scheme == "ircs": ssl = True
        if o.hostname is not None: args["host"] = o.hostname
        if o.port is not None: args["port"] = o.port
        if o.username is not None: args["username"] = o.username
        if o.password is not None: args["password"] = o.password

        modifiers = o.path.split(",")
        target = unquote(modifiers.pop(0)[1:])

        # Read query string
        params = parse_qs(o.query)

        if "msg" in params:
            if "on_connect" not in args:
                args["on_connect"] = []
            args["on_connect"].append("PRIVMSG %s :%s" % (target, params["msg"]))

        if "key" in params:
            if "channels" not in args:
                args["channels"] = []
            args["channels"].append((target, params["key"]))

        if "pass" in params:
            args["password"] = params["pass"]

        if "charset" in params:
            args["encoding"] = params["charset"]

        #
        if "channels" not in args and "isnick" not in modifiers:
            args["channels"] = [ target ]

        from nemubot.server.IRC import IRC as IRCServer
        srv = IRCServer(**args)

        if ssl:
            try:
                from ssl import create_default_context
                context = create_default_context()
            except ImportError:
                # Python 3.3 compat
                from ssl import SSLContext, PROTOCOL_TLSv1
                context = SSLContext(PROTOCOL_TLSv1)
            from ssl import wrap_socket
            srv._fd = context.wrap_socket(srv._fd, server_hostname=o.hostname)

    elif o.scheme == "matrix":
        # matrix://localpart:password@homeserver.tld/!room:homeserver.tld
        # matrix://localpart:password@homeserver.tld/%23alias:homeserver.tld
        # Use matrixs:// for https (default) vs http
        args = dict(init_args)

        homeserver = "https://" + o.hostname
        if o.port is not None:
            homeserver += ":%d" % o.port
        args["homeserver"] = homeserver

        if o.username is not None:
            args["user_id"] = o.username
        if o.password is not None:
            args["password"] = unquote(o.password)

        # Parse rooms from path (comma-separated, URL-encoded)
        if o.path and o.path != "/":
            rooms = [unquote(r) for r in o.path.lstrip("/").split(",") if r]
            if rooms:
                args.setdefault("channels", []).extend(rooms)

        params = parse_qs(o.query)
        if "token" in params:
            args["access_token"] = params["token"][0]
        if "nick" in params:
            args["nick"] = params["nick"][0]
        if "owner" in params:
            args["owner"] = params["owner"][0]

        from nemubot.server.Matrix import Matrix as MatrixServer
        srv = MatrixServer(**args)

    return srv
