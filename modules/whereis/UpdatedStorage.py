# coding=utf-8

import socket
from datetime import datetime
from datetime import timedelta

from .User import User

class UpdatedStorage:
  def __init__(self, url, port):
    sock = connect_to_ns(url, port)
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


def connect_to_ns(server, port):
  try:
    s = socket.socket()
    s.settimeout(3)
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
