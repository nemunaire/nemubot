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

from datetime import datetime
import re
import shlex

from response import Response

mgx = re.compile(b'''^(?:@(?P<tags>[^ ]+)\ )?
                      (?::(?P<prefix>
                         (?P<nick>[^!@ ]+)
                         (?: !(?P<user>[^@ ]+))?
                         (?:@(?P<host>[^ ]+))?
                      )\ )?
                      (?P<command>(?:[a-zA-Z]+|[0-9]{3}))
                      (?P<params>(?:\ [^:][^ ]*)*)(?:\ :(?P<trailing>.*))?
                 $''', re.X)

class Message:
  def __init__ (self, raw_line, timestamp, private=False):
    self.raw = raw_line
    self.private = private
    self.tags = { 'time': timestamp }
    self.params = list()

    p = mgx.match(raw_line.rstrip())

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
    if p.group("params"):
      for param in p.group("params").strip().split(b' '):
        self.params.append(param)

    if p.group("trailing"):
      self.params.append(p.group("trailing"))

    # Special commands
    if self.cmd == 'PRIVMSG' or self.cmd == 'NOTICE':
      self.receivers = self.decode(self.params[0]).split(',')

      # If CTCP, remove 0x01
      if len(self.params[1]) > 1 and (self.params[1][0] == 0x01 or self.params[1][1] == 0x01):
        self.is_ctcp = True
        self.text = self.decode(self.params[1][1:len(self.params[1])-1])
      else:
        self.is_ctcp = False
        self.text = self.decode(self.params[1])

      # Split content by words
      self.parse_content()

    elif self.cmd == '353': # RPL_NAMREPLY
      self.receivers = [ self.decode(self.params[0]) ]
      self.nicks = self.decode(self.params[1]).split(" ")

    elif self.cmd == '332':
      self.receivers = [ self.decode(self.params[0]) ]
      self.topic = self.decode(self.params[1]).split(" ")

    else:
      for i in range(0, len(self.params)):
        self.params[i] = self.decode(self.params[i])


  # TODO: here for legacy content
  @property
  def sender(self):
    return self.prefix
  @property
  def channel(self):
    return self.receivers[0]


  def parse_content(self):
      """Parse or reparse the message content"""
      # Remove !
      if self.text[0] == '!':
          self.qual = "cmd"
          self.text = self.text[1:].strip()

      # Split content by words
      try:
          self.cmds = shlex.split(self.text)
      except ValueError:
          self.cmds = self.text.split(' ')


  def decode(self, s):
    """Decode the content string usign a specific encoding"""
    if isinstance(s, bytes):
      try:
        s = s.decode()
      except UnicodeDecodeError:
        #TODO: use encoding from config file
        s = s.decode('utf-8', 'replace')
    return s
