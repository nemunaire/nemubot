# coding=utf-8

from module_state import ModuleState

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
