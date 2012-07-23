# coding=utf-8

class Channel:
  def __init__(self, node, srv):
    self.node = node
    self.name = node["name"]
    self.password = node["password"]
    self.people = dict()
    self.srv = srv
    self.topic = ""

  def join(self, nick, level = 0):
    #print ("%s arrive sur %s" % (nick, self.name))
    self.people[nick] = level

  def chtopic(self, newtopic):
    """Send command to change the topic"""
    self.srv.send_msg(self.name, newtopic, "TOPIC")
    self.topic = newtopic

  def nick(self, oldnick, newnick):
    #print ("%s change de nom pour %s" % (oldnick, newnick))
    if oldnick in self.people:
      lvl = self.people[oldnick]
      del self.people[oldnick]
    else:
      lvl = 0
    self.people[newnick] = lvl

  def part(self, nick):
    #print ("%s vient de quitter %s" % (self.sender, self.channel))
    if nick in self.people:
      del self.people[nick]

  def mode(self, msg):
    if msg.content[0] == "-k":
      self.password = ""
    elif msg.content[0] == "+k":
      if len(msg.content) > 1:
        self.password = ' '.join(msg.content[1:])[1:]
      else:
        self.password = msg.content[1]
    elif msg.content[0] == "+o":
      self.people[msg.nick] |= 4
    elif msg.content[0] == "-o":
      self.people[msg.nick] &= ~4
    elif msg.content[0] == "+h":
      self.people[msg.nick] |= 2
    elif msg.content[0] == "-h":
      self.people[msg.nick] &= ~2
    elif msg.content[0] == "+v":
      self.people[msg.nick] |= 1
    elif msg.content[0] == "-v":
      self.people[msg.nick] &= ~1

  def parse332(self, msg):
    self.topic = msg.content

  def parse353(self, msg):
    for p in msg.content:
      p = p.decode()
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
