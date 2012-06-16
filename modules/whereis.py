# coding=utf-8

import re
import sys
import socket
import time
import _thread
import threading
from datetime import datetime
from datetime import date
from datetime import timedelta
from urllib.parse import unquote

from module_state import ModuleState

nemubotversion = 3.0

THREAD = None
search = list()

class UpdatedStorage:
  def __init__(self):
    sock = connect_to_ns(CONF.getNode("server")["url"],
                         CONF.getNode("server").getInt("port"))
    self.users = dict()
    if sock != None:
      users = list_users(sock)
      if users is not None:
        for l in users:
          u = User(l)
          if u.login not in self.users:
            self.users[u.login] = list()
          self.users[u.login].append(u)
        self.lastUpdate = datetime.now ()
      else:
        self.users = None
      sock.close()
    else:
      self.users = None

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

def connect_to_ns(server, port):
  try:
    s = socket.socket()
    s.settimeout(1)
    s.connect((server, port))
  except socket.error:
    return None
  s.recv(8192)
  return s

def list_users(sock):
  try:
    sock.send('list_users\n'.encode())
    buf = ''
    while True:
        tmp = sock.recv(8192).decode()
        buf += tmp
        if '\nrep 002' in tmp or tmp == '':
            break
    return buf.split('\n')[:-2]
  except socket.error:
    return None


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
  if datas is None or datas.users is None:
    msg.send_chn("Hmm c'est embarassant, serait-ce la fin du monde ou juste netsoul qui est mort ?")
    return

  if msg.cmd[0] == "peoplein":
    peoplein(msg)
  elif msg.cmd[0] == "whoison" or msg.cmd[0] == "whoisin":
    whoison(msg)
  else:
    whereis_msg(msg)

  THREAD = None
  if len(search) > 0:
    startWhereis(search.pop())

def peoplein(msg):
  if len(msg.cmd) > 1:
    for sm in msg.cmd:
      sm = sm.lower()
      if sm == "peoplein":
        continue
      else:
        count = 0
        for userC in datas.users:
          for user in datas.users[userC]:
            usersm = user.sm
            if usersm is not None and usersm.lower() == sm:
              count += 1
        if count > 1:
          sOrNot = "s"
        else:
          sOrNot = ""
        msg.send_chn ("Il y a %d personne%s en %s." % (count, sOrNot, sm))

def whoison(msg):
  if len(msg.cmd) > 1:
    for pb in msg.cmd:
      pc = pb.lower()
      if pc == "whoison" or pc == "whoisin":
        continue
      else:
        found = list()
        for userC in datas.users:
          for user in datas.users[userC]:
            if (msg.cmd[0] == "whoison" and (user.ip[:len(pc)] == pc or user.location.lower() == pc)) or (msg.cmd[0] == "whoisin" and user.sm == pc):
              found.append(user.login)
        if len(found) > 0:
          if len(found) <= 15:
            if pc == "whoisin":
              msg.send_chn ("En %s, il y a %s" % (pb, ", ".join(found)))
            else:
              msg.send_chn ("%s correspond à %s" % (pb, ", ".join(found)))
          else:
            msg.send_chn ("%s: %d personnes" % (pb, len(found)))
        else:
          msg.send_chn ("%s: personne ne match ta demande :(" % (msg.sender))

DELAYED = dict()
delayEvnt = threading.Event()

class Delayed:
  def __init__(self):
    self.names = dict()

def whereis_msg(msg):
  names = list()
  for name in msg.cmd:
    if name == "whereis" or name == "whereare" or name == "ouest" or name == "ousont" or name == "ip":
      if len(msg.cmd) >= 2:
        continue
      else:
        name = msg.sender
    else:
      names.append(name)
  pasla = whereis(msg, names)
  if len(pasla) > 0:
    global DELAYED
    DELAYED[msg] = Delayed()
    for name in pasla:
      DELAYED[msg].names[name] = None
      #msg.srv.send_msg_prtn ("~whois %s" % name)
    msg.srv.send_msg_prtn ("~whois %s" % " ".join(pasla))
    startTime = datetime.now()
    names = list()
    while len(DELAYED[msg].names) > 0 and startTime + timedelta(seconds=4) > datetime.now():
      delayEvnt.clear()
      delayEvnt.wait(2)
      rem = list()
      for name in DELAYED[msg].names.keys():
        if DELAYED[msg].names[name] is not None:
          pasla = whereis(msg, (DELAYED[msg].names[name],))
          if len(pasla) != 0:
            names.append(pasla[0])
          rem.append(name)
      for r in rem:
        del DELAYED[msg].names[r]
    for name in DELAYED[msg].names.keys():
      if DELAYED[msg].names[name] is None:
        names.append(name)
      else:
        names.append(DELAYED[msg].names[name])
    if len(names) > 1:
      msg.send_chn ("%s ne sont pas connectés sur le PIE." % (", ".join(names)))
    else:
      for name in names:
        msg.send_chn ("%s n'est pas connecté sur le PIE." % name)
      

def whereis(msg, names):
  pasla = list()

  for name in names:
    if name in datas.users:
      if msg.cmd[0] == "ip":
        if len(datas.users[name]) == 1:
          msg.send_chn ("L'ip de %s est %s." %(name, datas.users[name][0].ip))
        else:
          out = ""
          for local in datas.users[name]:
            out += ", " + local.ip
          msg.send_chn ("%s est connecté à plusieurs endroits : %s." %(name, out[2:]))
      else:
        if len(datas.users[name]) == 1:
          msg.send_chn ("%s est %s (%s)." %(name, datas.users[name][0].poste, unquote(datas.users[name][0].location)))
        else:
          out = ""
          for local in datas.users[name]:
            out += ", " + local.poste + " (" + unquote(local.location) + ")"
          msg.send_chn ("%s est %s." %(name, out[2:]))
    else:
      pasla.append(name)

  return pasla


def parseanswer (msg):
  global datas, THREAD, search
  if msg.cmd[0] == "whereis" or msg.cmd[0] == "whereare" or msg.cmd[0] == "ouest" or msg.cmd[0] == "ousont" or msg.cmd[0] == "ip" or msg.cmd[0] == "peoplein" or msg.cmd[0] == "whoison" or msg.cmd[0] == "whoisin":
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
  if len(DELAYED) > 0 and msg.sender == msg.srv.partner:
    treat = False
    for part in msg.content.split(';'):
      if part is None:
        continue
      for d in DELAYED.keys():
        nKeys = list()
        for n in DELAYED[d].names.keys():
          nKeys.append(n)
        for n in nKeys:
          if DELAYED[d].names[n] is None and part.find(n) >= 0:
            result = re.match(".* est (.*[^.])\.?", part)
            if result is not None:
              DELAYED[d].names[n] = result.group(1)
              delayEvnt.set()
    return treat
  return False
