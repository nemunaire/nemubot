# coding=utf-8

COURSES = None

class Course:
  def __init__(self, iden):
    global COURSES
    if iden in COURSES.index:
      self.node = COURSES.index[iden]
    else:
      self.node = { "code":"N/A", "name":"N/A", "branch":"N/A" }

  @property
  def id(self):
    return self.node["xml:id"]

  @property
  def code(self):
    return self.node["code"]

  @property
  def name(self):
    return self.node["name"]

  @property
  def branch(self):
    return self.node["branch"]

  @property
  def validated(self):
    return int(self.node["validated"]) > 0
