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
import shlex

class Message:
  def __init__ (self, orig, private=False):
    self.cmd     = orig.cmd
    self.tags    = orig.tags
    self.params  = orig.params
    self.private = private
    self.prefix  = orig.prefix
    self.nick    = orig.nick

    # Special commands
    if self.cmd == 'PRIVMSG' or self.cmd == 'NOTICE':
      self.receivers = orig.decode(self.params[0]).split(',')

      # If CTCP, remove 0x01
      if len(self.params[1]) > 1 and (self.params[1][0] == 0x01 or self.params[1][1] == 0x01):
        self.is_ctcp = True
        self.text = orig.decode(self.params[1][1:len(self.params[1])-1])
      else:
        self.is_ctcp = False
        self.text = orig.decode(self.params[1])

      # Split content by words
      self.parse_content()

    else:
      for i in range(0, len(self.params)):
        self.params[i] = orig.decode(self.params[i])


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
      if len(self.text) > 1 and self.text[0] == '!':
          self.qual = "cmd"
          self.text = self.text[1:].strip()

      # Split content by words
      try:
          self.cmds = shlex.split(self.text)
      except ValueError:
          self.cmds = self.text.split(' ')
