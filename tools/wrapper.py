# coding=utf-8

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

from xmlparser.node import ModuleState

class Wrapper:
  """Simulate a hash table

  """

  def __init__(self):
    self.stateName = "state"
    self.attName = "name"
    self.cache = dict()

  def items(self):
    ret = list()
    for k in self.DATAS.index.keys():
      ret.append((k, self[k]))
    return ret

  def __contains__(self, i):
    return i in self.DATAS.index

  def __getitem__(self, i):
    return self.DATAS.index[i]

  def __setitem__(self, i, j):
    ms = ModuleState(self.stateName)
    ms.setAttribute(self.attName, i)
    j.save(ms)
    self.DATAS.addChild(ms)
    self.DATAS.setIndex(self.attName, self.stateName)

  def __delitem__(self, i):
    self.DATAS.delChild(self.DATAS.index[i])

  def save(self, i):
    if i in self.cache:
      self.cache[i].save(self.DATAS.index[i])
      del self.cache[i]

  def flush(self):
    """Remove all cached datas"""
    self.cache = dict()

  def reset(self):
    """Erase the list and flush the cache"""
    for child in self.DATAS.getNodes(self.stateName):
      self.DATAS.delChild(child)
    self.flush()
