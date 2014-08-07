# -*- coding: utf-8 -*-

# Nemubot is a modulable IRC bot, built around XML configuration files.
# Copyright (C) 2012  Mercier Pierre-Olivier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime
import re
import shlex
import time

import credits
from credits import Credits
from response import Response
import xmlparser

CREDITS = {}
filename = ""

def load(config_file):
  global CREDITS, filename
  CREDITS = dict ()
  filename = config_file
  credits.BANLIST = xmlparser.parse_file(filename)

def save():
  global filename
  credits.BANLIST.save(filename)


class Message:
  def __init__ (self, line, timestamp, private=False):
    self.raw = line
    self.time = timestamp
    self.channel = None
    self.content = b''
    self.ctcp = False
    line = line.rstrip() #remove trailing 'rn'

    words = line.split(b' ')
    if words[0][0] == 58: #58 is : in ASCII table
      self.sender = words[0][1:].decode()
      self.cmd = words[1].decode()
    else:
      self.cmd = words[0].decode()
      self.sender = None

    if self.cmd == 'PING':
      self.content = words[1]
    elif self.sender is not None:
      self.nick = (self.sender.split('!'))[0]
      if self.nick != self.sender:
        self.realname = (self.sender.split('!'))[1]
      else:
        self.realname = self.nick
        self.sender = self.nick + "!" + self.realname

      if len(words) > 2:
        self.channel = self.pickWords(words[2:]).decode()

      if self.cmd == 'PRIVMSG':
          # Check for CTCP request
          self.ctcp = len(words[3]) > 1 and (words[3][0] == 0x01 or words[3][1] == 0x01)
          self.content = self.pickWords(words[3:])
      elif self.cmd == '353' and len(words) > 3:
        for i in range(2, len(words)):
          if words[i][0] == 58:
            self.content = words[i:]
            #Remove the first :
            self.content[0] = self.content[0][1:]
            self.channel = words[i-1].decode()
            break
      elif self.cmd == 'NICK':
        self.content = self.pickWords(words[2:])
      elif self.cmd == 'MODE':
        self.content = words[3:]
      elif self.cmd == '332':
        self.channel = words[3]
        self.content = self.pickWords(words[4:])
      else:
        #print (line)
        self.content = self.pickWords(words[3:])
    else:
      print (line)
      if self.cmd == 'PRIVMSG':
        self.channel = words[2].decode()
        self.content = b' '.join(words[3:])
    self.decode()
    if self.cmd == 'PRIVMSG':
      self.parse_content()
    self.private = private

  def parse_content(self):
      """Parse or reparse the message content"""
      # If CTCP, remove 0x01
      if self.ctcp:
          self.content = self.content[1:len(self.content)-1]

      # Split content by words
      try:
          self.cmds = shlex.split(self.content)
      except ValueError:
          self.cmds = self.content.split(' ')

  def pickWords(self, words):
    """Parse last argument of a line: can be a single word or a sentence starting with :"""
    if len(words) > 0 and len(words[0]) > 0:
      if words[0][0] == 58:
        return b' '.join(words[0:])[1:]
      else:
        return words[0]
    else:
      return b''

  def decode(self):
    """Decode the content string usign a specific encoding"""
    if isinstance(self.content, bytes):
      try:
        self.content = self.content.decode()
      except UnicodeDecodeError:
        #TODO: use encoding from config file
        self.content = self.content.decode('utf-8', 'replace')

  def authorize_DEPRECATED(self):
      """Is nemubot listening for the sender on this channel?"""
      # TODO: deprecated
      if self.srv.isDCC(self.sender):
          return True
      elif self.realname not in CREDITS:
          CREDITS[self.realname] = Credits(self.realname)
      elif self.content[0] == '`':
          return True
      elif not CREDITS[self.realname].ask():
          return False
      return self.srv.accepted_channel(self.channel)

##############################
#                            #
#   Extraction/Format text   #
#                            #
##############################

  def just_countdown (self, delta, resolution = 5):
    sec = delta.seconds
    hours, remainder = divmod(sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    an = int(delta.days / 365.25)
    days = delta.days % 365.25

    sentence = ""
    force = False

    if resolution > 0 and (force or an > 0):
      force = True
      sentence += " %i an"%(an)

      if an > 1:
        sentence += "s"
      if resolution > 2:
        sentence += ","
      elif resolution > 1:
        sentence += " et"

    if resolution > 1 and (force or days > 0):
      force = True
      sentence += " %i jour"%(days)

      if days > 1:
        sentence += "s"
      if resolution > 3:
        sentence += ","
      elif resolution > 2:
        sentence += " et"

    if resolution > 2 and (force or hours > 0):
      force = True
      sentence += " %i heure"%(hours)
      if hours > 1:
        sentence += "s"
      if resolution > 4:
        sentence += ","
      elif resolution > 3:
        sentence += " et"

    if resolution > 3 and (force or minutes > 0):
      force = True
      sentence += " %i minute"%(minutes)
      if minutes > 1:
        sentence += "s"
      if resolution > 4:
        sentence += " et"

    if resolution > 4 and (force or seconds > 0):
      force = True
      sentence += " %i seconde"%(seconds)
      if seconds > 1:
        sentence += "s"
    return sentence[1:]


  def countdown_format (self, date, msg_before, msg_after, timezone = None):
    """Replace in a text %s by a sentence incidated the remaining time before/after an event"""
    if timezone != None:
      os.environ['TZ'] = timezone
      time.tzset()

    #Calculate time before the date
    if datetime.now() > date:
        sentence_c = msg_after
        delta = datetime.now() - date
    else:
        sentence_c = msg_before
        delta = date - datetime.now()

    if timezone != None:
      os.environ['TZ'] = "Europe/Paris"

    return sentence_c % self.just_countdown(delta)


  def extractDate (self):
    """Parse a message to extract a time and date"""
    msgl = self.content.lower ()
    result = re.match("^[^0-9]+(([0-9]{1,4})[^0-9]+([0-9]{1,2}|janvier|january|fevrier|février|february|mars|march|avril|april|mai|maï|may|juin|juni|juillet|july|jully|august|aout|août|septembre|september|october|octobre|oktober|novembre|november|decembre|décembre|december)([^0-9]+([0-9]{1,4}))?)[^0-9]+(([0-9]{1,2})[^0-9]*[h':]([^0-9]*([0-9]{1,2})([^0-9]*[m\":][^0-9]*([0-9]{1,2}))?)?)?.*$", msgl + " TXT")
    if result is not None:
      day = result.group(2)
      if len(day) == 4:
        year = day
        day = 0
      month = result.group(3)
      if month == "janvier" or month == "january" or month == "januar":
        month = 1
      elif month == "fevrier" or month == "février" or month == "february":
        month = 2
      elif month == "mars" or month == "march":
        month = 3
      elif month == "avril" or month == "april":
        month = 4
      elif month == "mai" or month == "may" or month == "maï":
        month = 5
      elif month == "juin" or month == "juni" or month == "junni":
        month = 6
      elif month == "juillet" or month == "jully" or month == "july":
        month = 7
      elif month == "aout" or month == "août" or month == "august":
        month = 8
      elif month == "september" or month == "septembre":
        month = 9
      elif month == "october" or month == "october" or month == "oktober":
        month = 10
      elif month == "november" or month == "novembre":
        month = 11
      elif month == "december" or month == "decembre" or month == "décembre":
        month = 12

      if day == 0:
        day = result.group(5)
      else:
        year = result.group(5)

      hour = result.group(7)
      minute = result.group(9)
      second = result.group(11)

      print ("Chaîne reconnue : %s/%s/%s %s:%s:%s"%(day, month, year, hour, minute, second))
      if year == None:
        year = date.today().year
      if hour == None:
        hour = 0
      if minute == None:
        minute = 0
      if second == None:
        second = 1
      else:
        second = int (second) + 1
        if second > 59:
          minute = int (minute) + 1
          second = 0

      return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
    else:
      return None
