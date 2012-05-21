# coding=utf-8

class ModuleException(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)


class ModuleState:
  def __init__(self, filename):
    self.filename = filename

    if not os.access(self.filename, os.R_OK):
      with open(self.filename) as f:
        for line in f:
          print line


class ModuleBase:
  def __init__(self, datas_path):
    self.datas_path = datas_path

    if self.module_name is None:
      raise ModuleException("module_name not defined")

    if self.conf is not None:
      self.conf = self.datas_path + self.conf
      if not os.access(self.conf, os.R_OK):
        


  def print(self, message):
    print ("[%s] %s" % (self.module_name, message))


  def load(self):
    return True

  def reload(self):
    return self.save() and self.load()

  def save(self):
    return True


  def launch(self, servers):
    return True

  def stop(self):
    return True


  def help_tiny(self):
    return None

  def help_full(self):
    return None


  def parseanswer(self, msg):
    return False

  def parseask(self, msg):
    return False

  def parselisten(self, msg):
    return False

  def parseadmin(self, msg):
    return False
