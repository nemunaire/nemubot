# coding=utf-8

class Channel:
  def __init__(self, node):
    self.node = node
    self.name = node["name"]
    self.password = node["password"]
    self.people = dict()
    self.topic = ""

  def join(self, msg):
    #print ("%s arrive sur %s" % (self.sender, self.channel))
    self.people[msg.sender] = 0

  def nick(self, msg):
    #print ("%s change de nom pour %s" % (self.sender, self.content))
    if msg.sender in self.people:
      lvl = self.people[msg.sender]
      del self.people[msg.sender]
    else:
      lvl = 0
    self.people[msg.content] = lvl

  def part(self, msg):
    #print ("%s vient de quitter %s" % (self.sender, self.channel))
    if msg.sender in self.people:
      del self.people[msg.sender]

  def mode(self, msg):
    if msg.content[0] == "-k":
      self.password = ""
    elif msg.content[0] == "+k":
      if len(msg.content) > 1:
        self.password = ' '.join(msg.content[1:])[1:]
      else:
        self.password = msg.content[1]
    elif msg.content[0] == "+o":
      self.people[msg.sender] |= 4
    elif msg.content[0] == "-o":
      self.people[msg.sender] &= ~4
    elif msg.content[0] == "+h":
      self.people[msg.sender] |= 2
    elif msg.content[0] == "-h":
      self.people[msg.sender] &= ~2
    elif msg.content[0] == "+v":
      self.people[msg.sender] |= 1
    elif msg.content[0] == "-v":
      self.people[msg.sender] &= ~1

  def parse332(self, msg):
    self.topic = msg.content

  def parse353(self, msg):
    for p in msg.content:
      if p[0] == "@":
        level = 4
      elif p[0] == "%":
        level = 2
      elif p[0] == "+":
        level = 1
      else:
        self.people[p] = 0
        continue
      self.people[p[1:]] = level
