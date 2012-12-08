# coding=utf-8

import xml.sax
from datetime import datetime
from datetime import date
import time

class ModuleState:
  """Tiny tree representation of an XML file"""

  def __init__(self, name):
    self.name = name
    self.content = ""
    self.attributes = dict()
    self.childs = list()
    self.index = dict()
    self.index_fieldname = None
    self.index_tagname = None

  def getName(self):
    """Get the name of the current node"""
    return self.name

  def display(self, level = 0):
    ret = ""
    out = list()
    for k in self.attributes:
      out.append("%s : %s" % (k, self.attributes[k]))
    ret += "%s%s { %s } = '%s'\n" % (' ' * level, self.name, ' ; '.join(out), self.content)
    for c in self.childs:
      ret += c.display(level + 2)
    return ret

  def __str__(self):
    return self.display()

  def __getitem__(self, i):
    """Return the attribute asked"""
    return self.getAttribute(i)

  def __setitem__(self, i, c):
    """Set the attribute"""
    return self.setAttribute(i, c)

  def getAttribute(self, name):
    """Get the asked argument or return None if doesn't exist"""
    if name in self.attributes:
      return self.attributes[name]
    else:
      return None

  def getDate(self, name):
    """Get the asked argument and return it as a date"""
    if name in self.attributes.keys():
      if isinstance(self.attributes[name], datetime):
        return self.attributes[name]
      else:
        try:
          return datetime.fromtimestamp(float(self.attributes[name]))
        except ValueError:
         while True:
          try:
            return datetime.fromtimestamp(time.mktime(time.strptime(self.attributes[name][:19], "%Y-%m-%d %H:%M:%S")))
          except ImportError:
            pass
    else:
      return None

  def getInt(self, name):
    """Get the asked argument and return it as an integer"""
    if name in self.attributes.keys():
      return int(float(self.attributes[name]))
    else:
      return None

  def getBool(self, name):
    """Get the asked argument and return it as an integer"""
    if name in self.attributes.keys():
        return (isinstance(self.attributes[name], bool) and self.attributes[name]) or self.attributes[name] == "True"
    else:
        return False

  def setIndex(self, fieldname = "name", tagname = None):
    """Defines an hash table to accelerate childs search. You have just to define a common attribute"""
    self.index = dict()
    self.index_fieldname = fieldname
    self.index_tagname = tagname
    for child in self.childs:
      if (tagname is None or tagname == child.name) and child.hasAttribute(fieldname):
        self.index[child[fieldname]] = child

  def __contains__(self, i):
    """Return true if i is found in the index"""
    return i in self.index

  def hasAttribute(self, name):
    """DOM like method"""
    return (name in self.attributes)

  def setAttribute(self, name, value):
    """DOM like method"""
    self.attributes[name] = value

  def getContent(self):
    return self.content

  def getChilds(self):
    """Return a full list of direct child of this node"""
    return self.childs

  def getNode(self, tagname):
    """Get a unique node (or the last one) with the given tagname"""
    ret = None
    for child in self.childs:
      if tagname is None or tagname == child.name:
        ret = child
    return ret

  def getFirstNode(self, tagname):
    """Get a unique node (or the last one) with the given tagname"""
    for child in self.childs:
      if tagname is None or tagname == child.name:
        return child
    return None

  def getNodes(self, tagname):
    """Get all direct childs that have the given tagname"""
    ret = list()
    for child in self.childs:
      if tagname is None or tagname == child.name:
        ret.append(child)
    return ret

  def hasNode(self, tagname):
    """Return True if at least one node with the given tagname exists"""
    ret = list()
    for child in self.childs:
      if tagname is None or tagname == child.name:
        return True
    return False

  def addChild(self, child):
    """Add a child to this node"""
    self.childs.append(child)
    if self.index_fieldname is not None:
      self.setIndex(self.index_fieldname, self.index_tagname)

  def delChild(self, child):
    """Remove the given child from this node"""
    self.childs.remove(child)
    if self.index_fieldname is not None:
      self.setIndex(self.index_fieldname, self.index_tagname)

  def save_node(self, gen):
    """Serialize this node as a XML node"""
    attribs = {}
    for att in self.attributes.keys():
        if att[0] != "_": # Don't save attribute starting by _
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
    """Save the current node as root node in a XML file"""
    with open(filename,"w") as f:
      gen = xml.sax.saxutils.XMLGenerator(f, "utf-8")
      gen.startDocument()
      self.save_node(gen)
      gen.endDocument()
