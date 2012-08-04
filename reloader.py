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

import imp

import credits
import channel
import DCC
import message
import module_state
import module_states_file
import prompt
import server

def reload():
  imp.reload(credits)
  imp.reload(channel)
  imp.reload(DCC)
  imp.reload(message)
  imp.reload(module_state)
  imp.reload(module_states_file)
  imp.reload(prompt)
  imp.reload(server)

