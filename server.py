import sys
import traceback
import socket
import threading
import time
import imp

message = __import__("message")
imp.reload(message)
channel = __import__("channel")
imp.reload(channel)

class Server(threading.Thread):
    def __init__(self, node, nick, owner, realname, socket = None):
      self.stop = False
      self.stopping = threading.Event()
      self.nick = nick
      self.owner = owner
      self.realname = realname
      self.s = socket
      self.connected = self.s is not None
      self.node = node

      self.listen_nick = True

      self.channels = dict()
      for chn in node.getNodes("channel"):
        chan = channel.Channel(chn)
        self.channels[chan.name] = chan

      threading.Thread.__init__(self)

    @property
    def host(self):
      if self.node.hasAttribute("server"):
        return self.node["server"]
      else:
        return "localhost"

    @property
    def port(self):
      if self.node.hasAttribute("port"):
        return self.node.getInt("port")
      else:
        return "6667"

    @property
    def password(self):
      if self.node.hasAttribute("password"):
        return self.node["password"]
      else:
        return None

    @property
    def partner(self):
      if self.node.hasAttribute("partner"):
        return self.node["partner"]
      else:
        return None

    @property
    def id(self):
        return self.host + ":" + str(self.port)

    def send_ctcp_response(self, me, to, msg, cmd = "NOTICE", endl = "\r\n"):
      if msg is not None and channel is not None:
        for line in msg.split("\n"):
          if line != "":
            self.s.send ((":%s %s %s :%s%s" % (me, cmd, to, line, endl)).encode ())

    def send_msg_final(self, channel, msg, cmd = "PRIVMSG", endl = "\r\n"):
        if channel == self.nick:
            print ("\033[1;35mWarning:\033[0m Nemubot talks to himself: %s" % msg)
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
        for channel in self.channels.keys():
            self.send_msg (channel, msg, cmd, endl)


    def accepted_channel(self, chan):
        if self.listen_nick:
            return chan in self.channels or chan == self.nick
        else:
            return chan in self.channels

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
            #Send a message in order to close the socket
            self.s.send(("WHO %s\r\n" % self.nick).encode ())
            self.stopping.wait()
            return True
        else:
            return False

    def join(self, chan, password = None):
        if chan is not None and self.connected and chan not in self.channels:
            chn = xmlparser.module_state.Module_State("channel")
            chn["name"] = chan
            chn["password"] = password
            self.node.addChild(chn)
            self.channels[chan] = channel.Channel(chn)
            if password is not None:
                self.s.send(("JOIN %s %s\r\n" % (chan, password)).encode ())
            else:
                self.s.send(("JOIN %s\r\n" % chan).encode ())
            return True
        else:
            return False

    def leave(self, chan):
        if chan is not None and self.connected and chan in self.channels:
            self.s.send(("PART %s\r\n" % self.channels[chan].name).encode ())
            del self.channels[chan]
            return True
        else:
            return False

    def update_mods(self, mods):
        self.mods = mods

    def launch(self, mods):
        if not self.connected:
            self.stop = False
            self.mods = mods
            self.start()
        else:
            print ("  Already connected.")

    def run(self):
      if not self.connected:
          self.s = socket.socket() #Create the socket
          self.s.connect((self.host, self.port)) #Connect to server
          self.stopping.clear()
          self.connected = True

          if self.password != None:
              self.s.send(b"PASS " + self.password.encode () + b"\r\n")
          self.s.send(("NICK %s\r\n" % self.nick).encode ())
          self.s.send(("USER %s %s bla :%s\r\n" % (self.nick, self.host, self.realname)).encode ())
          print ("Connection to %s:%d completed" % (self.host, self.port))

          if len(self.channels) > 0:
              for chn in self.channels.keys():
                  if self.channels[chn].password is not None:
                      self.s.send(("JOIN %s %s\r\n" % (self.channels[chn].name, self.channels[chn].password)).encode ())
                  else:
                      self.s.send(("JOIN %s\r\n" % self.channels[chn].name).encode ())
          print ("Listen to channels: %s" % ' '.join (self.channels.keys()))

      readbuffer = "" #Here we store all the messages from server
      while not self.stop:
        try:
            raw = self.s.recv(1024) #recieve server messages
            data = raw.decode()
            if not data:
                break
        except UnicodeDecodeError:
            try:
                data = raw.decode("utf-8", "replace")
            except UnicodeDecodeError:
                print ("\033[1;31mERROR:\033[0m while decoding of: %s"%data)
                continue
        readbuffer = readbuffer + data
        temp = readbuffer.split("\n")
        readbuffer = temp.pop( )

        for line in temp:
          try:
              msg = message.Message (self, line)
              msg.treat (self.mods)
          except:
              print ("\033[1;31mERROR:\033[0m occurred during the processing of the message: %s"%line)
              exc_type, exc_value, exc_traceback = sys.exc_info()
              traceback.print_exception(exc_type, exc_value, exc_traceback)
      if self.connected:
          self.s.close()
          self.connected = False
          print ("Server `%s' successfully stopped." % self.id)
      self.stopping.set()
      #Rearm Thread
      threading.Thread.__init__(self)
