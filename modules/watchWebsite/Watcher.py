# coding=utf-8

from datetime import datetime
import threading

class Watcher(threading.Thread):
  def __init__(self):
    self.servers = list()
    self.stop = False
    self.newSrv = threading.Event()
    threading.Thread.__init__(self)

  def addServer(self, server):
    self.servers.append(server)
    self.newSrv.set()

  def check(self, closer):
    closer.check()
    self.newSrv.set()

  def run(self):
    while not self.stop:
      self.newSrv.clear()
      closer = None
      #Gets the closer server update
      for server in self.servers:
        if server.update < datetime.now():
          #print ("Closer now: %s à %s"%(server.url, server.update))
          self.check(server)
        elif closer is None or server.update < closer.update:
          closer = server
      if closer is not None:
        #print ("Closer: %s à %s"%(closer.url, closer.update))
        timeleft = (closer.update - datetime.now()).seconds
        timer = threading.Timer(timeleft, self.check, (closer,))
        timer.start()
        #print ("Start timer (%ds)"%timeleft)

      self.newSrv.wait()

      if closer is not None and closer.update is not None and closer.update > datetime.now():
        timer.cancel()

  def stop(self):
    self.stop = True
    self.newSrv.set()
