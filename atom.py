#!/usr/bin/python3
# coding=utf-8

import time
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation

class AtomEntry:
  def __init__ (self, node):
    self.id = node.getElementsByTagName("id")[0].firstChild.nodeValue
    self.title = node.getElementsByTagName("title")[0].firstChild.nodeValue
    try:
      self.updated = time.strptime(node.getElementsByTagName("updated")[0].firstChild.nodeValue[:19], "%Y-%m-%dT%H:%M:%S")
    except:
      try:
        self.updated = time.strptime(node.getElementsByTagName("updated")[0].firstChild.nodeValue[:10], "%Y-%m-%d")
      except:
        print (node.getElementsByTagName("updated")[0].firstChild.nodeValue[:10])
        self.updated = time.localtime ()
    if len(node.getElementsByTagName("summary")) > 0:
      self.summary = node.getElementsByTagName("summary")[0].firstChild.nodeValue
    else:
      self.summary = None
    if len(node.getElementsByTagName("link")) > 0:
      self.link = node.getElementsByTagName("link")[0].getAttribute ("href")
    else:
      self.link = None
    if len (node.getElementsByTagName("category")) >= 1:
      self.category = node.getElementsByTagName("category")[0].getAttribute ("term")
    else:
      self.category = None
    if len (node.getElementsByTagName("link")) > 1:
      self.link2 = node.getElementsByTagName("link")[1].getAttribute ("href")
    else:
      self.link2 = None

class Atom:
  def __init__ (self, string):
    self.feed = parseString (string).documentElement
    self.id = self.feed.getElementsByTagName("id")[0].firstChild.nodeValue
    self.title = self.feed.getElementsByTagName("title")[0].firstChild.nodeValue

    self.updated = None
    self.entries = dict ()
    for item in self.feed.getElementsByTagName("entry"):
      entry = AtomEntry (item)
      self.entries[entry.id] = entry
      if self.updated is None or self.updated < entry.updated:
        self.updated = entry.updated

  def diff (self, other):
    differ = list ()
    for k in other.entries.keys ():
      if self.updated is None and k not in self.entries:
        self.updated = other.entries[k].updated
      if k not in self.entries and other.entries[k].updated >= self.updated:
        differ.append (other.entries[k])
    return differ


if __name__ == "__main__":
  content1 = ""
  with open("rss.php.1", "r") as f:
    for line in f:
      content1 += line
  content2 = ""
  with open("rss.php", "r") as f:
    for line in f:
      content2 += line
  a = Atom (content1)
  print (a.updated)
  b = Atom (content2)
  print (b.updated)

  diff = a.diff (b)
  print (diff)
