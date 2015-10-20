# -*- coding: utf-8 -*-

# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2015  Mercier Pierre-Olivier
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

from datetime import datetime, timezone
import re
import shlex

import nemubot.message as message
from nemubot.server.message.abstract import Abstract

mgx = re.compile(b'''^(?:@(?P<tags>[^ ]+)\ )?
                      (?::(?P<prefix>
                         (?P<nick>[^!@ ]+)
                         (?: !(?P<user>[^@ ]+))?
                         (?:@(?P<host>[^ ]*))?
                      )\ )?
                      (?P<command>(?:[a-zA-Z]+|[0-9]{3}))
                      (?P<params>(?:\ [^:][^ ]*)*)(?:\ :(?P<trailing>.*))?
                 $''', re.X)

class IRC(Abstract):

    """Class responsible for parsing IRC messages"""

    def __init__(self, raw, encoding="utf-8"):
        self.encoding = encoding
        self.tags = { 'time': datetime.now(timezone.utc) }
        self.params = list()

        p = mgx.match(raw.rstrip())

        if p is None:
            raise Exception("Not a valid IRC message: %s" % raw)

        # Parse tags if exists: @aaa=bbb;ccc;example.com/ddd=eee
        if p.group("tags"):
            for tgs in self.decode(p.group("tags")).split(';'):
                tag = tgs.split('=')
                if len(tag) > 1:
                    self.add_tag(tag[0], tag[1])
                else:
                    self.add_tag(tag[0])

        # Parse prefix if exists: :nick!user@host.com
        self.prefix = self.decode(p.group("prefix"))
        self.nick   = self.decode(p.group("nick"))
        self.user   = self.decode(p.group("user"))
        self.host   = self.decode(p.group("host"))

        # Parse command
        self.cmd = self.decode(p.group("command"))

        # Parse params
        if p.group("params") is not None and p.group("params") != b'':
            for param in p.group("params").strip().split(b' '):
                self.params.append(param)

        if p.group("trailing") is not None:
            self.params.append(p.group("trailing"))


    def add_tag(self, key, value=None):
        """Add an IRCv3.2 Message Tags

        Arguments:
        key -- tag identifier (unique for the message)
        value -- optional value for the tag
        """

        # Treat special tags
        if key == "time" and value is not None:
            import calendar, time
            value = datetime.fromtimestamp(calendar.timegm(time.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")), timezone.utc)

        # Store tag
        self.tags[key] = value


    @property
    def is_ctcp(self):
        """Analyze a message, to determine if this is a CTCP one"""
        return self.cmd == "PRIVMSG" and len(self.params) == 2 and len(self.params[1]) > 1 and (self.params[1][0] == 0x01 or self.params[1][1] == 0x01)


    def decode(self, s):
        """Decode the content string usign a specific encoding

        Argument:
        s -- string to decode
        """

        if isinstance(s, bytes):
            try:
                s = s.decode()
            except UnicodeDecodeError:
                s = s.decode(self.encoding, 'replace')
        return s



    def to_server_string(self, client=True):
        """Pretty print the message to close to original input string

        Keyword argument:
        client -- export as a client-side string if true
        """

        res = ";".join(["@%s=%s" % (k, v if not isinstance(v, datetime) else v.strftime("%Y-%m-%dT%H:%M:%S.%fZ")) for k, v in self.tags.items()])

        if not client:
            res += " :%s!%s@%s" % (self.nick, self.user, self.host)

        res += " " + self.cmd

        if len(self.params) > 0:

            if len(self.params) > 1:
                res += " " + self.decode(b" ".join(self.params[:-1]))
            res += " :" + self.decode(self.params[-1])

        return res


    def to_bot_message(self, srv):
        """Convert to one of concrete implementation of AbstractMessage

        Argument:
        srv -- the server from the message was received
        """

        if self.cmd == "PRIVMSG" or self.cmd == "NOTICE":

            receivers = self.decode(self.params[0]).split(',')

            common_args = {
                "server": srv.id,
                "date": self.tags["time"],
                "to": receivers,
                "to_response": [r if r != srv.nick else self.nick for r in receivers],
                "frm": self.nick
            }

            # If CTCP, remove 0x01
            if self.is_ctcp:
                text = self.decode(self.params[1][1:len(self.params[1])-1])
            else:
                text = self.decode(self.params[1])

            if text.find(srv.nick) == 0 and len(text) > len(srv.nick) + 2 and text[len(srv.nick)] == ":":
                designated = srv.nick
                text = text[len(srv.nick) + 1:].strip()
            else:
                designated = None

            # Is this a command?
            if len(text) > 1 and text[0] == '!':
                text = text[1:].strip()

                # Split content by words
                try:
                    args = shlex.split(text)
                except ValueError:
                    args = text.split(' ')

                # Extract explicit named arguments: @key=value or just @key
                kwargs = {}
                for i in range(len(args) - 1, 0, -1):
                    arg = args[i]
                    if len(arg) > 2:
                        if arg[0:1] == '\\@':
                            args[i] = arg[1:]
                        elif arg[0] == '@':
                            arsp = arg[1:].split("=", 1)
                            if len(arsp) == 2:
                                kwargs[arsp[0]] = arsp[1]
                            else:
                                kwargs[arg[1:]] = None
                            args.pop(i)

                return message.Command(cmd=args[0],
                                       args=args[1:],
                                       kwargs=kwargs,
                                       **common_args)

            # Is this an ask for this bot?
            elif designated is not None:
                return message.DirectAsk(designated=designated, message=text, **common_args)

            # Normal message
            else:
                return message.Text(message=text, **common_args)

        return None
