# coding=utf-8

from datetime import datetime
import threading

newStrendEvt = threading.Event()

class Manager(threading.Thread):
  def __init__(self, datas, srvs):
    self.stop = False
    self.DATAS = datas
    self.SRVS = srvs
    threading.Thread.__init__(self)

  def alertEnd(self, evt):
    global newStrendEvt
    #Send the message on each matched servers
    for server in self.SRVS.keys():
      if not evt.hasAttribute("server") or server == evt["server"]:
        if evt["channel"] == self.SRVS[server].nick:
          self.SRVS[server].send_msg_usr(evt["proprio"], "%s: %s arrivé à échéance." % (evt["proprio"], evt["name"]))
        else:
          self.SRVS[server].send_msg(evt["channel"], "%s: %s arrivé à échéance." % (evt["proprio"], evt["name"]))
    self.DATAS.delChild(self.DATAS.index[evt["name"]])
    save()
    newStrendEvt.set()

  def run(self):
    global newStrendEvt
    while not self.stop:
      newStrendEvt.clear()
      closer = None
      #Gets the closer event
      for evt in self.DATAS.index.keys():
        if self.DATAS.index[evt].hasAttribute("end") and (closer is None or self.DATAS.index[evt].getDate("end") < closer.getDate("end")) and self.DATAS.index[evt].getDate("end") > datetime.now():
          closer = self.DATAS.index[evt]
      if closer is not None and closer.hasAttribute("end"):
        #print ("Closer: %s à %s"%(closer.name, closer["end"]))
        timeleft = (closer.getDate("end") - datetime.now()).seconds
        timer = threading.Timer(timeleft, self.alertEnd, (closer,))
        timer.start()
        #print ("Start timer (%ds)"%timeleft)

      newStrendEvt.wait()

      if closer is not None and closer.hasAttribute("end") and closer.getDate("end") > datetime.now():
        timer.cancel()
    self.threadManager = None
