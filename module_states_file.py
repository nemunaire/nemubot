#!/usr/bin/python3
# coding=utf-8

import os
import xml.sax

from module_exception import ModuleException
from module_state import ModuleState

class ModuleStatesFile(xml.sax.ContentHandler):
  def startDocument(self):
    self.root = None
    self.stack = list()

  def startElement(self, name, attrs):
    cur = ModuleState(name)

    for name in attrs.keys():
      cur.setAttribute(name, attrs.getValue(name))

    self.stack.append(cur)

  def endElement(self, name):
    child = self.stack.pop()
    size = len(self.stack)
    if size > 0:
      self.stack[size - 1].addChild(child)
    else:
      self.root = child

def parse_file(filename):
  parser = xml.sax.make_parser()
  mod = ModuleStatesFile()
  parser.setContentHandler(mod)
  try:
    parser.parse(open(filename, "r"))
    return mod.root
  except:
    return ModuleState("nemubotstate")
