# -*- coding: utf-8 -*-

# Nemubot is a modulable IRC bot, built around XML configuration files.
# Copyright (C) 2012  Mercier Pierre-Olivier
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

import json
import random
import shlex
import urllib.parse
import zlib

from DCC import DCC
import hooks
from response import Response

class NetworkBot:
    def __init__(self, context, srv, dest, dcc=None):
        # General informations
        self.context = context
        self.srv = srv
        self.dest = dest

        self.dcc = dcc # DCC connection to the other bot
        self.hooks = list()
        self.REGISTERED_HOOKS = list()

        # Tags monitor
        self.my_tag = random.randint(0,255)
        self.inc_tag = 0
        self.tags = dict()

    @property
    def sender(self):
        if self.dcc is not None:
            return self.dcc.sender
        return None

    @property
    def nick(self):
        if self.dcc is not None:
            return self.dcc.nick
        return None

    @property
    def realname(self):
        if self.dcc is not None:
            return self.dcc.realname
        return None

    def isDCC(self, someone):
        """Abstract implementation"""
        return True

    def send_cmd(self, cmd, data=None):
        """Create a tag and send the command"""
        # First, define a tag
        self.inc_tag = (self.inc_tag + 1) % 256
        while self.inc_tag in self.tags:
            self.inc_tag = (self.inc_tag + 1) % 256
        tag = ("%c%c" % (self.my_tag, self.inc_tag)).encode()

        self.tags[tag] = (cmd, data)

        # Send the command with the tag
        self.send_response_final(tag, cmd)

    def send_response(self, res, tag):
        self.send_response_final(tag, [res.sender, res.channel, res.nick, res.nomore, res.title, res.more, res.count, json.dumps(res.messages)])

    def msg_treated(self, tag):
        self.send_ack(tag)

    def send_response_final(self, tag, msg):
        """Send a response with a tag"""
        if isinstance(msg, list):
            cnt = b''
            for i in msg:
                if i is None:
                    cnt += b' ""'
                elif isinstance(i, int):
                    cnt += (' %d' % i).encode()
                elif isinstance(i, float):
                    cnt += (' %f' % i).encode()
                else:
                    cnt += b' "' + urllib.parse.quote(i).encode() + b'"'
                if False and len(cnt) > 10:
                    cnt = b' Z ' + zlib.compress(cnt)
                    print (cnt)
            self.dcc.send_dcc_raw(tag + cnt)
        else:
            for line in msg.split("\n"):
                self.dcc.send_dcc_raw(tag + b' ' + line.encode())

    def send_ack(self, tag):
        """Acknowledge a command"""
        if tag in self.tags:
            del self.tags[tag]
        self.send_response_final(tag, "ACK")

    def connect(self):
        """Making the connexion with dest through srv"""
        if self.dcc is None or not self.dcc.connected:
            self.dcc = DCC(self.srv, self.dest)
            self.dcc.treatement = self.hello
            self.dcc.send_dcc("NEMUBOT###")
        else:
            self.send_cmd("FETCH")

    def disconnect(self, reason=""):
        """Close the connection and remove the bot from network list"""
        del self.context.network[self.dcc.id]
        self.dcc.send_dcc("DISCONNECT :%s" % reason)
        self.dcc.disconnect()

    def hello(self, line):
        if line == b'NEMUBOT###':
            self.dcc.treatement = self.treat_msg
            self.send_cmd("MYTAG %c" % self.my_tag)
            self.send_cmd("FETCH")
        elif line != b'Hello ' + self.srv.nick.encode() + b'!':
            self.disconnect("Sorry, I think you were a bot")

    def treat_msg(self, line, cmd=None):
        words = line.split(b' ')

        # Ignore invalid commands
        if len(words) >= 2:
            tag = words[0]

            # Is it a response?
            if tag in self.tags:
                # Is it compressed content?
                if words[1] == b'Z':
                    #print (line)
                    line = zlib.decompress(line[len(tag) + 3:])
                self.response(line, tag, [urllib.parse.unquote(arg) for arg in shlex.split(line[len(tag) + 1:].decode())], self.tags[tag])
            else:
                cmd = words[1]
                if len(words) > 2:
                    args = shlex.split(line[len(tag) + len(cmd) + 2:].decode())
                    args = [urllib.parse.unquote(arg) for arg in args]
                else:
                    args = list()
                #print ("request:", line)
                self.request(tag, cmd, args)

    def response(self, line, tag, args, t):
        (cmds, data) = t
        #print ("response for", cmds, ":", args)

        if isinstance(cmds, list):
            cmd = cmds[0]
        else:
            cmd = cmds
            cmds = list(cmd)

        if args[0] == 'ACK': # Acknowledge a command
            del self.tags[tag]

        elif cmd == "FETCH" and len(args) >= 5:
            level = int(args[1])
            while len(self.hooks) <= level:
                self.hooks.append(hooks.MessagesHook(self.context))

            if args[2] == "": args[2] = None
            if args[3] == "": args[3] = None
            if args[4] == "": args[4] = list()
            else: args[4] = args[4].split(',')

            self.hooks[level].add_hook(args[0], hooks.Hook(self.exec_hook, args[2], None, args[3], args[4]), self)

        elif cmd == "HOOK" and len(args) >= 8:
            # Rebuild the response
            if args[1] == '': args[1] = None
            if args[2] == '': args[2] = None
            if args[3] == '': args[3] = None
            if args[4] == '': args[4] = None
            if args[5] == '': args[5] = None
            if args[6] == '': args[6] = None
            res = Response(args[0], channel=args[1], nick=args[2], nomore=args[3], title=args[4], more=args[5], count=args[6])
            for msg in json.loads(args[7]):
                res.append_message(msg)
            if len(res.messages) <= 1:
                res.alone = True
            self.srv.send_response(res, None)


    def request(self, tag, cmd, args):
        # Parse
        if cmd == b'MYTAG' and len(args) > 0: # Inform about choosen tag
            while args[0] == self.my_tag:
                self.my_tag = random.randint(0,255)
            self.send_ack(tag)

        elif cmd == b'FETCH': # Get known commands
            for name in ["cmd_hook", "ask_hook", "msg_hook"]:
                elts = self.context.create_cache(name)
                for elt in elts:
                    (hooks, lvl, store) = elts[elt]
                    for h in hooks:
                        self.send_response_final(tag, [name, lvl, elt, h.regexp, ','.join(h.channels)])
            self.send_ack(tag)

        elif (cmd == b'HOOK' or cmd == b'"HOOK"') and len(args) > 0: # Action requested
            self.context.receive_message(self, args[0].encode(), True, tag)


    def exec_hook(self, msg):
        self.send_cmd(["HOOK", msg.raw])
