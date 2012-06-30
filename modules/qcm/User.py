# coding=utf-8

USERS = None

class User:
  def __init__(self, iden):
    global USERS
    if iden in USERS.index:
      self.node = USERS.index[iden]
    else:
      self.node = { "username":"N/A", "email":"N/A" }

  @property
  def id(self):
    return self.node["xml:id"]

  @property
  def username(self):
    return self.node["username"]

  @property
  def email(self):
    return self.node["email"]

  @property
  def validated(self):
    return int(self.node["validated"]) > 0
