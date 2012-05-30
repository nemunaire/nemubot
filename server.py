import sys
import traceback
import socket
import threading
import time
import imp

message = __import__("message")
imp.reload(message)

class Server(threading.Thread):
    def __init__(self, server, nick, owner, realname):
      self.stop = False
      self.stopping = threading.Event()
      self.connected = False
      self.nick = nick
      self.owner = owner
      self.realname = realname

      if server.hasAttribute("server"):
        self.host = server.getAttribute("server")
      else:
        self.host = "localhost"
      if server.hasAttribute("port"):
        self.port = int(server.getAttribute("port"))
      else:
        self.port = 6667
      if server.hasAttribute("password"):
        self.password = server.getAttribute("password")
      else:
        self.password = None

      self.listen_nick = True
      self.partner = "nbr23"

      self.channels = list()
      for channel in server.getChilds():
        self.channels.append(channel.getAttribute("name"))

      threading.Thread.__init__(self)

    @property
    def id(self):
        return self.host + ":" + str(self.port)

    def send_ctcp_response(self, me, to, msg, cmd = "NOTICE", endl = "\r\n"):
      if msg is not None and channel is not None:
        for line in msg.split("\n"):
          if line != "":
            self.s.send ((":%s %s %s :%s%s" % (me, cmd, to, line, endl)).encode ())

    def send_msg_final(self, channel, msg, cmd = "PRIVMSG", endl = "\r\n"):
        if msg is not None and channel is not None:
            for line in msg.split("\n"):
                if line != "":
                    self.s.send (("%s %s :%s%s" % (cmd, channel, line, endl)).encode ())

    def send_msg_prtn (self, msg):
        self.send_msg_final(self.partner, msg)

    def send_msg_usr (self, user, msg):
        if user is not None and user[0] != "#":
            self.send_msg_final(user, msg)

    def send_msg (self, channel, msg, cmd = "PRIVMSG", endl = "\r\n"):
        if self.accepted_channel(channel):
            self.send_msg_final(channel, msg, cmd, endl)

    def send_global (self, msg, cmd = "PRIVMSG", endl = "\r\n"):
        for channel in self.channels:
            self.send_msg (channel, msg, cmd, endl)


    def accepted_channel(self, channel):
        if self.listen_nick:
            return self.channels.count(channel) or channel == self.nick
        else:
            return self.channels.count(channel)

    def disconnect(self):
        if self.connected:
            self.stop = True
            self.s.shutdown(socket.SHUT_RDWR)
            self.stopping.wait()
            return True
        else:
            return False

    def join(self, channel):
        if channel is not None and self.connected:
            self.channels.append(channel)
            self.s.send(("JOIN %s\r\n" % channel).encode ())
            return True
        else:
            return False

    def leave(self, channel):
        if channel is not None and self.connected and channel in self.channels:
            self.channels.remove(channel)
            self.s.send(("PART %s\r\n" % channel.split()[0]).encode ())
            return True
        else:
            return False

    def update_mods(self, mods):
        self.mods = mods

    def launch(self, mods):
        if not self.connected:
            self.stop = False
            #self.datas_dir = datas_dir #DEPRECATED
            self.mods = mods
            self.start()
        else:
            print ("  Already connected.")

    def run(self):
      self.s = socket.socket( ) #Create the socket
      self.s.connect((self.host, self.port)) #Connect to server
      self.stopping.clear()
      self.connected = True

      if self.password != None:
        self.s.send(b"PASS " + self.password.encode () + b"\r\n")
      self.s.send(("NICK %s\r\n" % self.nick).encode ())
      self.s.send(("USER %s %s bla :%s\r\n" % (self.nick, self.host, self.realname)).encode ())
      print ("Connection to %s:%d completed with version 2.0" % (self.host, self.port))

      if len(self.channels) > 0:
          self.s.send(("JOIN %s\r\n" % ' '.join (self.channels)).encode ())
      print ("Listen to channels: %s" % ' '.join (self.channels))

      readbuffer = "" #Here we store all the messages from server
      while not self.stop:
        try:
            readbuffer = readbuffer + self.s.recv(1024).decode() #recieve server messages
        except UnicodeDecodeError:
            print ("ERREUR de décodage unicode")
            continue
        temp = readbuffer.split("\n")
        readbuffer = temp.pop( )

        for line in temp:
          try:
              msg = message.Message (self, line)
              msg.treat (self.mods)
          except:
              print ("Une erreur est survenue lors du traitement du message : %s"%line)
              exc_type, exc_value, exc_traceback = sys.exc_info()
              traceback.print_exception(exc_type, exc_value, exc_traceback)
      self.connected = False
      print ("Server `%s' successfully stopped." % self.id)
      self.stopping.set()
      #Rearm Thread
      threading.Thread.__init__(self)
