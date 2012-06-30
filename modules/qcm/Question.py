# coding=utf-8

from datetime import datetime
import hashlib
import http.client
import socket
from urllib.parse import quote

from .Course import Course
from .User import User

QUESTIONS = None

class Question:
  def __init__(self, node):
    self.node = node

  @property
  def ident(self):
    return self.node["xml:id"]

  @property
  def id(self):
    return self.node["xml:id"]

  @property
  def question(self):
    return self.node["question"]

  @property
  def course(self):
    return Course(self.node["course"])

  @property
  def answers(self):
    return self.node.getNodes("answer")

  @property
  def validator(self):
    return User(self.node["validator"])

  @property
  def writer(self):
    return User(self.node["writer"])

  @property
  def validated(self):
    return self.node["validated"]

  @property
  def addedtime(self):
    return datetime.fromtimestamp(float(self.node["addedtime"]))

  @property
  def author(self):
    return User(self.node["writer"])

  def report(self, raison="Sans raison"):
    conn = http.client.HTTPConnection(CONF.getNode("server")["url"])
    try:
      conn.request("GET", "report.php?id=" + hashlib.md5(self.id.encode()).hexdigest() + "&raison=" + quote(raison))
    except socket.gaierror:
      print ("[%s] impossible de récupérer la page %s."%(s, p))
      return False
    res = conn.getresponse()
    conn.close()
    return (res.status == http.client.OK)

  @property
  def tupleInfo(self):
    return (self.author.username, self.validator.username, self.addedtime)

  @property
  def bestAnswer(self):
    best = self.answers[0]
    for answer in self.answers:
      if best.getInt("score") < answer.getInt("score"):
        best = answer
    return best["answer"]

  def isCorrect(self, msg):
    msg = msg.lower().replace(" ", "")
    for answer in self.answers:
      if msg == answer["answer"].lower().replace(" ", ""):
        return True
    return False

  def getScore(self, msg):
    msg = msg.lower().replace(" ", "")
    for answer in self.answers:
      if msg == answer["answer"].lower().replace(" ", ""):
        return answer.getInt("score")
    return 0
