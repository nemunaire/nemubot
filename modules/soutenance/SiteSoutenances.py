# coding=utf-8

from datetime import datetime
from datetime import timedelta
import re
import time

from .Soutenance import Soutenance

class SiteSoutenances:
  def __init__(self, page):
    save = False
    self.souts = list()
    self.updated = datetime.now()
    last = None
    for line in page.split("\n"):
      if re.match("</tr>", line) is not None:
        save = False
      elif re.match("<tr.*>", line) is not None:
        save = True
        last = Soutenance()
        self.souts.append(last)
      elif save:
        result = re.match("<td[^>]+>(.*)</td>", line)
        if last.hour is None:
          try:
            last.hour = datetime.fromtimestamp(time.mktime(time.strptime(result.group(1), "%Y-%m-%d  %H:%M")))
          except ValueError:
            continue
        elif last.rank == 0:
          last.rank = int (result.group(1))
        elif last.login == None:
          last.login = result.group(1)
        elif last.state == None:
          last.state = result.group(1)
        elif last.assistant == None:
          last.assistant = result.group(1)
        elif last.start == None:
          try:
            last.start = datetime.fromtimestamp(time.mktime(time.strptime(result.group(1), "%Y-%m-%d  %H:%M")))
          except ValueError:
            last.start = None
        elif last.end == None:
          try:
            last.end = datetime.fromtimestamp(time.mktime(time.strptime(result.group(1), "%Y-%m-%d  %H:%M")))
          except ValueError:
            last.end = None
          
  def update(self):
    if self.findLast() is not None and datetime.now () - self.updated > timedelta(minutes=2):
      return None
    elif datetime.now () - self.updated < timedelta(hours=1):
      return self
    else:
      return None

  def findAssistants(self):
    h = {}
    for s in self.souts:
      if s.assistant is not None and s.assistant != "":
        h[s.assistant] = (s.start, s.end)
    return h
    

  def findLast(self):
    close = None
    for s in self.souts:
      if (s.state != "En attente" and s.start is not None and (close is None or close.rank < s.rank or close.hour.day > s.hour.day)) and (close is None or s.hour - close.hour < timedelta(seconds=2499)):
        close = s
    return close

  def findAll(self, login):
    ss = list()
    for s in self.souts:
      if s.login == login:
        ss.append(s)
    return ss

  def findClose(self, login):
    ss = self.findAll(login)
    close = None
    for s in ss:
      if close is not None:
        print (close.hour)
      print (s.hour)
      if close is None or (close.hour < s.hour and close.hour.day >= datetime.datetime().day):
        close = s
    return close
