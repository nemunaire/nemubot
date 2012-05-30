# coding=utf-8

import xml.sax
from datetime import datetime
from datetime import date
import time

class ModuleState:
  def __init__(self, name):
    self.name = name
    self.attributes = dict()
    self.childs = list()
    self.index = dict()
    self.index_fieldname = None
    self.index_tagname = None

  def getName(self):
    return self.name

  def __getitem__(self, i):
    return self.getAttribute(i)

  def __contains__(self, i):
    return i in self.index

  def getAttribute(self, name):
    if name in self.attributes:
      return self.attributes[name]
    else:
      return None

  def getDate(self, name):
    if name in self.attributes.keys():
      if isinstance(self.attributes[name], datetime):
        return self.attributes[name]
      else:
        return date.fromtimestamp(float(self.attributes[name]))
    else:
      return None

  def getInt(self, name):
    if name in self.attributes.keys():
      return int(self.attributes[name])
    else:
      return None

  def setIndex(self, fieldname = "name", tagname = None):
    self.index_fieldname = fieldname
    self.index_tagname = tagname
    for child in self.childs:
      if (tagname is None or tagname == child.name) and child.hasAttribute(fieldname):
        self.index[child[fieldname]] = child

  def hasAttribute(self, name):
    return (name in self.attributes)

  def setAttribute(self, name, value):
    self.attributes[name] = value

  def getChilds(self):
    return self.childs

  def getNode(self, tagname):
    ret = None
    for child in self.childs:
      if tagname is None or tagname == child.name:
        ret = child
    return ret

  def getNodes(self, tagname):
    ret = list()
    for child in self.childs:
      if tagname is None or tagname == child.name:
        ret.append(child)
    return ret

  def addChild(self, child):
    self.childs.append(child)
    if self.index_fieldname is not None:
      self.setIndex(self.index_fieldname, self.index_tagname)

  def save_node(self, gen):
    attribs = {}
    for att in self.attributes.keys():
      if isinstance(self.attributes[att], datetime):
        attribs[att] = str(time.mktime(self.attributes[att].timetuple()))
      else:
        attribs[att] = str(self.attributes[att])
    attrs = xml.sax.xmlreader.AttributesImpl(attribs)

    gen.startElement(self.name, attrs)

    for child in self.childs:
      child.save_node(gen)

    gen.endElement(self.name)

  def save(self, filename):
    with open(filename,"w") as f:
      gen = xml.sax.saxutils.XMLGenerator(f, "utf-8")
      gen.startDocument()
      self.save_node(gen)
      gen.endDocument()
