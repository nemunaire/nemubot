import imp
import socket
import threading
import time

message = __import__("message")
imp.reload(message)

PORTS = list()

class DCC(threading.Thread):
  def __init__(self, srv, dest, socket = None):
    self.DCC = False
    self.error = False
    self.stop = False
    self.stopping = threading.Event()
    self.s = socket
    self.connected = self.s is not None
    self.conn = None
    self.messages = list()

    self.named = dest
    if self.named is not None:
      self.dest = (self.named.split('!'))[0]
      if self.dest != self.named:
        self.realname = (self.named.split('!'))[1]
      else:
        self.realname = self.dest

    self.srv = srv

    self.port = self.foundPort()

    if self.port is None:
      print ("No more available slot for DCC connection")
      self.setError("Il n'y a plus de place disponible sur le serveur pour initialiser une session DCC.")
      
    threading.Thread.__init__(self)

  def foundPort(self):
    for p in range(65432, 65535):
      if p not in PORTS:
        PORTS.append(p)
        return p
    return None

  @property
  def isDCC(self):
    return self.DCC and not self.error

  @property
  def nick(self):
    return self.srv.nick

  @property
  def id(self):
    return self.srv.id + "/" + self.named

  def setError(self, msg):
    self.error = True
    self.srv.send_msg_usr(dest, msg)

  def send_ctcp(self, to, line, cmd = None, endl = None):
    if cmd is None: self.srv.send_ctcp(to, line)
    elif endl is None: self.srv.send_ctcp(to, line, cmd)
    else: self.srv.send_ctcp(to, line, cmd, endl)

  def send_dcc(self, msg, to = None):
    if to is None or to == self.named or to == self.dest:
      if self.error:
        self.srv.send_msg_final(self.dest, msg)
      elif not self.connected or self.conn is None:
        if not self.DCC:
          self.start()
          self.DCC = True
        self.messages.append(msg)
      else:
        for line in msg.split("\n"):
          self.conn.sendall(line.encode() + b'\n')
    else:
      self.srv.send_dcc(msg, to)

  def send_msg_final(self, channel, msg, cmd = None, endl = None):
    if channel == self.named or channel == self.dest:
      self.send_dcc(msg, channel)
    else:
      if cmd is None: self.srv.send_msg_final(to, line)
      elif endl is None: self.srv.send_msg_final(to, line, cmd)
      else: self.srv.send_msg_final(to, line, cmd, endl)

  def send_msg_prtn(self, msg):
    self.srv.send_msg_prtn(msg)

  def send_msg_usr(self, user, msg):
    if user == self.named or user == self.dest:
      self.send_dcc(msg, user)
    else:
      self.srv.send_msg_usr(user, msg)

  def send_msg (self, channel, msg, cmd = None, endl = None):
    if cmd is None: self.srv.send_msg(channel, line)
    elif endl is None: self.srv.send_msg(channel, line, cmd)
    else: self.srv.send_msg(channel, line, cmd, endl)

  def send_global (self, msg, cmd = None, endl = None):
    if cmd is None: self.srv.send_global(channel, line)
    elif endl is None: self.srv.send_global(channel, line, cmd)
    else: self.srv.send_global(channel, line, cmd, endl)

  def accepted_channel(self, chan):
    self.srv.accepted_channel(chan)

  def disconnect(self):
    if self.connected:
      self.stop = True
      self.s.shutdown(socket.SHUT_RDWR)
      self.stopping.wait()
      return True
    else:
      return False

  def kill(self):
    if self.connected:
      self.stop = True
      self.connected = False
      #self.stopping.wait()#Compare with server before delete me
      return True
    else:
      return False

  def join(self, chan, password = None):
    self.srv.join(chan, password)

  def leave(self, chan):
    self.srv.leave(chan)

  def update_mods(self, mods):
    self.srv.update_mods(mods)

  def launch(self, mods = None):
    if not self.connected:
      self.stop = False
      self.start()

  def run(self):
    self.stopping.clear()
    #Open the port
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      self.s.bind(('', self.port))
    except:
      try:
        self.port = self.foundPort()
        self.s.bind(('', self.port))
      except:
        self.setError("Une erreur s'est produite durant la tentative d'ouverture d'une session DCC.")
        return
    print ('Listen on', self.port, "for", self.named)

    #Send CTCP request for DCC
    self.srv.send_ctcp(self.dest, "DCC CHAT CHAT 1488679878 %d" % self.port, "PRIVMSG")

    self.s.listen(1)
    #Waiting for the client
    (self.conn, addr) = self.s.accept()
    print ('Connected by', addr)
    self.connected = True

    #Start by sending all queued messages
    for mess in self.messages:
      self.send_dcc(mess)

    time.sleep(1)

    readbuffer = b''
    while not self.stop:
      raw = self.conn.recv(1024) #recieve server messages
      if not raw:
        break
      readbuffer = readbuffer + raw
      temp = readbuffer.split(b'\n')
      readbuffer = temp.pop()

      for line in temp:
        self.srv.treat_msg((":%s PRIVMSG %s :" % (self.named, self.srv.nick)).encode() + line, self)

    if self.connected:
      self.conn.close()
      self.connected = False
    self.stopping.set()
    #Rearm Thread
    threading.Thread.__init__(self)
