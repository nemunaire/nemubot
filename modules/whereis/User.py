# coding=utf-8

class User(object):
  def __init__(self, line):
    fields = line.split()
    self.login = fields[1]
    self.ip = fields[2]
    self.location = fields[8]
    self.promo = fields[9]

  @property
  def sm(self):
    for sm in CONF.getNodes("sm"):
      if self.ip.startswith(sm["ip"]):
        return sm["name"]
    return None

  @property
  def poste(self):
    if self.sm is None:
      if self.ip.startswith('10.'):
        return 'quelque part sur le PIE (%s)'%self.ip
      else:
        return "chez lui"
    else:
      if self.ip.startswith('10.247') or self.ip.startswith('10.248') or self.ip.startswith('10.249') or self.ip.startswith('10.250'):
        return "en " + self.sm + " rangée " + self.ip.split('.')[2] + " poste " + self.ip.split('.')[3]
      else:
        return "en " + self.sm

  def __cmp__(self, other):
    return cmp(self.login, other.login)
    
  def __hash__(self):
    return hash(self.login)
