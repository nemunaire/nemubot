import sys
import traceback
import socket
import _thread
import time

import message

#class WaitedAnswer:
#    def __init__(self, channel):
#        self.channel = channel
#        self.module

class Server:
    def __init__(self, server, nick, owner, realname):
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

      self.waited_answer = list()

      self.listen_nick = True
      self.partner = "nbr23"

      self.channels = list()
      for channel in server.getElementsByTagName('channel'):
        self.channels.append(channel.getAttribute("name"))

    @property
    def id(self):
        return self.host + ":" + str(self.port)

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


    def register_answer(self, channel, ):
        self.waited_answer.append(channel)

    def launch(self, mods, datas_dir):
      self.datas_dir = datas_dir
      _thread.start_new_thread(self.connect, (mods,))

    def accepted_channel(self, channel):
        if self.listen_nick:
            return self.channels.count(channel) or channel == self.nick
        else:
            return self.channels.count(channel)

    def read(self, mods):
      self.readbuffer = "" #Here we store all the messages from server
      while 1:
        try:
            self.readbuffer = self.readbuffer + self.s.recv(1024).decode() #recieve server messages
        except UnicodeDecodeError:
            print ("ERREUR de décodage unicode")
            continue
        temp = self.readbuffer.split("\n")
        self.readbuffer = temp.pop( )

        for line in temp:
          msg = message.Message (self, line)
          try:
              msg.treat (mods)
          except:
              print ("Une erreur est survenue lors du traitement du message : %s"%line)
              exc_type, exc_value, exc_traceback = sys.exc_info()
              traceback.print_exception(exc_type, exc_value, exc_traceback)


    def connect(self, mods):
      self.s = socket.socket( ) #Create the socket
      self.s.connect((self.host, self.port)) #Connect to server

      if self.password != None:
        self.s.send(b"PASS " + self.password.encode () + b"\r\n")
      self.s.send(("NICK %s\r\n" % self.nick).encode ())
      self.s.send(("USER %s %s bla :%s\r\n" % (self.nick, self.host, self.realname)).encode ())
      print ("Connection to %s:%d completed" % (self.host, self.port))

      self.s.send(("JOIN %s\r\n" % ' '.join (self.channels)).encode ())
      print ("Listen to channels: %s" % ' '.join (self.channels))

      self.read(mods)
