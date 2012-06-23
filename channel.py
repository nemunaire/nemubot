# coding=utf-8

class Channel:
  def __init__(self, node):
    self.node = node
    self.name = node["name"]
    self.password = node["password"]
    self.people = list()
    self.topic = ""
