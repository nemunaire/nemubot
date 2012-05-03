# coding=utf-8

import re
import sys
import socket
import time
import _thread
from datetime import datetime
from datetime import date
from datetime import timedelta
from urllib.parse import unquote
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation

NS_SERVER = 'ns-server.epita.fr'
NS_PORT = 4242

THREAD = None
search = list()

class UpdatedStorage:
  def __init__(self):
    sock = connect_to_ns(NS_SERVER, NS_PORT)
    self.users = dict()
    if sock != None:
      for l in list_users(sock):
        u = User(l)
        self.users[u.login] = u
      sock.close()
      self.lastUpdate = datetime.now ()

  def update(self):
    if datetime.now () - self.lastUpdate < timedelta(minutes=10):
      return self
    else:
      return None


class User(object):
    def __init__(self, line):
        fields = line.split()
        self.login = fields[1]
        self.ip = fields[2]
        self.location = fields[8]
        self.promo = fields[9]

    @property
    def sm(self):
        if self.ip.startswith('10.200'):
            return 'en SM' + self.ip.split('.')[2]
        elif self.ip.startswith('10.247'):
            return 'en pasteur'
        elif self.ip.startswith('10.248'):
            return 'en srlab'
        elif self.ip.startswith('10.249'):
            return 'en midlab'
        elif self.ip.startswith('10.250'):
            return 'en cisco'
        elif self.ip.startswith('10.41'):
            return 'sur le wifi'
        else:
            return None

    @property
    def poste(self):
      if self.sm is None:
        if self.ip.startswith('10'):
            return 'quelque part sur le PIE (%s)'%self.ip
        else:
            return "chez lui"
      else:
        if self.ip.startswith('10.200'):
          return self.sm + " poste " + self.ip.split('.')[3]
        else:
          return self.sm + " rangée " + self.ip.split('.')[2] + " poste " + self.ip.split('.')[3]

    def __cmp__(self, other):
        return cmp(self.login, other.login)
    
    def __hash__(self):
        return hash(self.login)

def connect_to_ns(server, port):
  try:
    s = socket.socket()
    s.settimeout(1)
    s.connect((server, port))
  except socket.error:
    return None
  s.recv(8192) # salut ...
  return s

def list_users(sock):
    sock.send('list_users\n'.encode())
    buf = ''
    while True:
        tmp = sock.recv(8192).decode()
        buf += tmp
        if '\nrep 002' in tmp or tmp == '':
            break
    return buf.split('\n')[:-2]


def load_module(datas_path):
  """Load this module"""
  return

def save_module():
  """Save the module state"""
  if THREAD is not None:
    THREAD.exit()
  return

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Find a user on the PIE"

def help_full ():
  return "!whereis /who/: gives the position of /who/.\n!whereare /who/ [/other who/ ...]: gives the position of /who/."

datas = None

def startWhereis(msg):
  global datas, THREAD, search
  if datas is not None:
    datas = datas.update ()
  if datas is None:
    datas = UpdatedStorage()
  if datas is None:
    msg.send_chn("Hmm c'est embarassant, serait-ce la fin du monde ou juste netsoul qui est mort ?")
    return

  pasla = list()

  for name in msg.cmd:
    if name == "whereis" or name == "whereare" or name == "ouest" or name == "ousont" or name == "ip":
      if len(msg.cmd) >= 2:
        continue
      else:
        name = msg.sender

    if name in datas.users:
      if msg.cmd[0] == "ip":
        msg.send_chn ("L'ip de %s est %s." %(name, datas.users[name].ip))
      else:
        msg.send_chn ("%s est %s (%s)." %(name, datas.users[name].poste, unquote(datas.users[name].location)))
    else:
      pasla.append(name)

  if len(pasla) == 1:
    msg.send_chn ("%s n'est pas connecté sur le PIE." % pasla[0])
  elif len(pasla) > 1:
    msg.send_chn ("%s ne sont pas connectés sur le PIE." % ", ".join(pasla))

  THREAD = None
  if len(search) > 0:
    startWhereis(search.pop())


def parseanswer (msg):
  global datas, THREAD, search
  if msg.cmd[0] == "whereis" or msg.cmd[0] == "whereare" or msg.cmd[0] == "ouest" or msg.cmd[0] == "ousont" or msg.cmd[0] == "ip":
    if len(msg.cmd) > 10:
      msg.send_snd ("Demande moi moins de personnes à la fois dans ton !%s" % msg.cmd[0])
      return True

    if THREAD is None:
      THREAD = _thread.start_new_thread (startWhereis, (msg,))
    else:
      search.append(msg)
    return True
  return False

def parseask (msg):
  return False

def parselisten (msg):
  return False
