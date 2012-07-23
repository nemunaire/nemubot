import imp
import os
import re
import socket
import sys
import threading
import time
import traceback

message = __import__("message")
imp.reload(message)

#Store all used ports
PORTS = list()

class DCC(threading.Thread):
  def __init__(self, srv, dest, socket = None):
    self.DCC = False
    self.error = False
    self.stop = False
    self.stopping = threading.Event()
    self.conn = socket
    self.connected = self.conn is not None
    self.messages = list()

    self.sender = dest
    if self.sender is not None:
      self.nick = (self.sender.split('!'))[0]
      if self.nick != self.sender:
        self.realname = (self.sender.split('!'))[1]
      else:
        self.realname = self.nick

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
  def id(self):
    return self.srv.id + "/" + self.sender

  def setError(self, msg):
    self.error = True
    self.srv.send_msg_usr(dest, msg)

  def disconnect(self):
    if self.connected:
      self.stop = True
      self.conn.shutdown(socket.SHUT_RDWR)
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

  def launch(self, mods = None):
    if not self.connected:
      self.stop = False
      self.start()

  def accept_user(self, host, port):
    self.conn = socket.socket()
    try:
      self.conn.connect((host, port))
      print ('Accepted user from', host, port, "for", self.sender)
      self.connected = True
      self.stop = False
    except:
      self.connected = False
      self.error = True
      return False
    self.start()
    return True


  def request_user(self, type="CHAT", filename="CHAT", size=""):
    #Open the port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      s.bind(('', self.port))
    except:
      try:
        self.port = self.foundPort()
        s.bind(('', self.port))
      except:
        self.setError("Une erreur s'est produite durant la tentative d'ouverture d'une session DCC.")
        return
    print ('Listen on', self.port, "for", self.sender)

    #Send CTCP request for DCC
    self.srv.send_ctcp(self.nick, "DCC %s %s %d %d %s" % (type, filename, self.srv.ip, self.port, size), "PRIVMSG")

    s.listen(1)
    #Waiting for the client
    (self.conn, addr) = s.accept()
    print ('Connected by', addr)
    self.connected = True

  def send_dcc(self, msg, to = None):
    if to is None or to == self.sender or to == self.nick:
      if self.error:
        self.srv.send_msg_final(self.nick, msg)
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

  def send_file(self, filename):
    if os.path.isfile(filename):
      self.messages = filename
      if not self.DCC:
        self.start()
        self.DCC = True
    else:
      print("File not found `%s'" % filename)

  def run(self):
    self.stopping.clear()
    if not isinstance(self.messages, list):
      self.request_user("SEND", os.path.basename(self.messages), os.path.getsize(self.messages))
      if self.connected:
        with open(self.messages, 'rb') as f:
          d = f.read(268435456) #Packets size: 256Mo
          while d:
            self.conn.sendall(d)
            self.conn.recv(4) #The client send a confirmation after each packet
            d = f.read(268435456) #Packets size: 256Mo
    else:
      self.request_user()

      #Start by sending all queued messages
      for mess in self.messages:
        self.send_dcc(mess)

      time.sleep(1)

      readbuffer = b''
      nicksize = len(self.srv.nick)
      Bnick = self.srv.nick.encode()
      while not self.stop:
        raw = self.conn.recv(1024) #recieve server messages
        if not raw:
          break
        readbuffer = readbuffer + raw
        temp = readbuffer.split(b'\n')
        readbuffer = temp.pop()

        for line in temp:
          if line[:nicksize] == Bnick and line[nicksize+1:].strip()[:10] == b'my name is':
            name = line[nicksize+1:].strip()[11:].decode('utf-8', 'replace')
            if re.match("^[a-zA-Z0-9_-]+$", name):
              if name not in self.srv.dcc_clients:
                del self.srv.dcc_clients[self.sender]
                self.nick = name
                if len(self.sender.split("!")) > 1:
                  self.sender = self.nick + "!" + self.sender.split("!")[1]
                else:
                  self.sender = self.nick
                self.srv.dcc_clients[self.sender] = self
                self.send_dcc("Hi "+self.nick)
              else:
                self.send_dcc("This nickname is already in use, please choose another one.")
            else:
              self.send_dcc("The name you entered contain invalid char.")
          else:
            self.srv.treat_msg((":%s PRIVMSG %s :" % (self.sender, self.srv.nick)).encode() + line, self.srv, True)

    if self.connected:
      self.conn.close()
      self.connected = False
    self.stopping.set()
    #Rearm Thread
    threading.Thread.__init__(self)
