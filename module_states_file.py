#!/usr/bin/python3
# coding=utf-8

import os
import imp
import xml.sax

module_state = __import__("module_state")
imp.reload(module_state)

class ModuleStatesFile(xml.sax.ContentHandler):
  def startDocument(self):
    self.root = None
    self.stack = list()

  def startElement(self, name, attrs):
    cur = module_state.ModuleState(name)

    for name in attrs.keys():
      cur.setAttribute(name, attrs.getValue(name))

    self.stack.append(cur)

  def characters(self, content):
    self.stack[len(self.stack)-1].content += content

  def endElement(self, name):
    child = self.stack.pop()
    size = len(self.stack)
    if size > 0:
      self.stack[size - 1].content = self.stack[size - 1].content.strip()
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
    if mod.root is None:
      return module_state.ModuleState("nemubotstate")
    else:
      return mod.root

def parse_string(string):
  mod = ModuleStatesFile()
  try:
    xml.sax.parseString(string, mod)
    return mod.root
  except:
    if mod.root is None:
      return module_state.ModuleState("nemubotstate")
    else:
      return mod.root
