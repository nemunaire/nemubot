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
from DCC import DCC
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
  def __init__ (self, srv, line, timestamp, private = False):
    self.raw = line
    self.srv = srv
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
        #Check for CTCP request
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
    self.private = private or (self.channel is not None and self.srv is not None and self.channel == self.srv.nick)

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

  @property
  def is_owner(self):
      return self.nick == self.srv.owner

  def authorize(self):
      """Is nemubot listening for the sender on this channel?"""
      if self.srv.isDCC(self.sender):
          return True
      elif self.realname not in CREDITS:
          CREDITS[self.realname] = Credits(self.realname)
      elif self.content[0] == '`':
          return True
      elif not CREDITS[self.realname].ask():
          return False
      return self.srv.accepted_channel(self.channel)

  def treat(self):
      """Parse and treat the message"""
      if self.cmd == "PING":
          self.srv.send_pong(self.content)
      elif self.cmd == "PRIVMSG" and self.ctcp:
          self.parsectcp()
      elif self.cmd == "PRIVMSG" and self.authorize():
          return self.parsemsg()
      elif self.channel in self.srv.channels:
          if self.cmd == "353":
              self.srv.channels[self.channel].parse353(self)
          elif self.cmd == "332":
              self.srv.channels[self.channel].parse332(self)
          elif self.cmd == "MODE":
              self.srv.channels[self.channel].mode(self)
          elif self.cmd == "JOIN":
              self.srv.channels[self.channel].join(self.nick)
          elif self.cmd == "PART":
              self.srv.channels[self.channel].part(self.nick)
          elif self.cmd == "TOPIC":
              self.srv.channels[self.channel].topic = self.content
      elif self.cmd == "NICK":
          for chn in self.srv.channels.keys():
              self.srv.channels[chn].nick(self.nick, self.content)
      elif self.cmd == "QUIT":
          for chn in self.srv.channels.keys():
              self.srv.channels[chn].part(self.nick)
      return None

  def parsectcp(self):
      """Parse CTCP requests"""
      if self.content == '\x01CLIENTINFO\x01':
          self.srv.send_ctcp(self.sender, "CLIENTINFO TIME USERINFO VERSION CLIENTINFO")
      elif self.content == '\x01TIME\x01':
          self.srv.send_ctcp(self.sender, "TIME %s" % (datetime.now()))
      elif self.content == '\x01USERINFO\x01':
          self.srv.send_ctcp(self.sender, "USERINFO %s" % (self.srv.realname))
      elif self.content == '\x01VERSION\x01':
          self.srv.send_ctcp(self.sender, "VERSION nemubot v%s" % self.srv.context.version_txt)
      elif self.content[:9] == '\x01DCC CHAT':
          words = self.content[1:len(self.content) - 1].split(' ')
          ip = self.srv.toIP(int(words[3]))
          conn = DCC(self.srv, self.sender)
          if conn.accept_user(ip, int(words[4])):
              self.srv.dcc_clients[conn.sender] = conn
              conn.send_dcc("Hello %s!" % conn.nick)
          else:
              print ("DCC: unable to connect to %s:%s" % (ip, words[4]))
      elif self.content == '\x01NEMUBOT\x01':
          self.srv.send_ctcp(self.sender, "NEMUBOT %f" % self.srv.context.version)
      elif self.content[:7] != '\x01ACTION':
          print (self.content)
          self.srv.send_ctcp(self.sender, "ERRMSG Unknown or unimplemented CTCP request")

  def reparsemsg(self):
      self.parsemsg()

  def parsemsg (self):
    self.srv.context.treat_pre(self)
    #Treat all messages starting with 'nemubot:' as distinct commands
    if self.content.find("%s:"%self.srv.nick) == 0:
      #Remove the bot name
      self.content = self.content[len(self.srv.nick)+1:].strip()
      messagel = self.content.lower()

      # Treat ping
      if re.match(".*(m[' ]?entends?[ -]+tu|h?ear me|do you copy|ping)",
                  messagel) is not None:
          return Response(self.sender, message="pong", channel=self.channel, nick=self.nick)

      # Ask hooks
      else:
          return self.srv.context.treat_ask(self)

    #Owner commands
    elif self.content[0] == '`' and self.sender == self.srv.owner:
      self.cmd = self.content[1:].split(' ')
      if self.cmd[0] == "ban":
        if len(self.cmd) > 1:
          credits.BANLIST.append(self.cmd[1])
        else:
          print (credits.BANLIST)
      elif self.cmd[0] == "banlist":
          print (credits.BANLIST)
      elif self.cmd[0] == "unban":
        if len(self.cmd) > 1:
          credits.BANLIST.remove(self.cmd[1])

      elif self.cmd[0] == "credits":
        if len(self.cmd) > 1 and self.cmd[1] in CREDITS:
          self.send_chn ("%s a %d crédits." % (self.cmd[1], CREDITS[self.cmd[1]]))
        else:
          for c in CREDITS.keys():
            print (CREDITS[c].to_string())

    #Messages stating with !
    elif self.content[0] == '!' and len(self.content) > 1:
      try:
        self.cmd = shlex.split(self.content[1:])
      except ValueError:
        self.cmd = self.content[1:].split(' ')
      if self.cmd[0] == "help":
          res = Response(self.sender)
          if len(self.cmd) > 1:
              if self.cmd[1] in self.srv.context.modules:
                  if len(self.cmd) > 2:
                      if hasattr(self.srv.context.modules[self.cmd[1]], "HELP_cmd"):
                          res.append_message(self.srv.context.modules[self.cmd[1]].HELP_cmd(self, self.cmd[2]))
                      else:
                          res.append_message("No help for command %s in module %s" % (self.cmd[2], self.cmd[1]))
                  elif hasattr(self.srv.context.modules[self.cmd[1]], "help_full"):
                      res.append_message(self.srv.context.modules[self.cmd[1]].help_full())
                  else:
                      res.append_message("No help for module %s" % self.cmd[1])
              else:
                  res.append_message("No module named %s" % self.cmd[1])
          else:
              res.append_message("Pour me demander quelque chose, commencez "
                                 "votre message par mon nom ; je réagis "
                                 "également à certaine commandes commençant par"
                                 " !.  Pour plus d'informations, envoyez le "
                                 "message \"!more\".")
              res.append_message("Mon code source est libre, publié sous "
                                 "licence AGPL (http://www.gnu.org/licenses/). "
                                 "Vous pouvez le consulter, le dupliquer, "
                                 "envoyer des rapports de bogues ou bien "
                                 "contribuer au projet sur GitHub : "
                                 "http://github.com/nemunaire/nemubot/")
              res.append_message(title="Pour plus de détails sur un module, "
                                 "envoyez \"!help nomdumodule\". Voici la liste"
                                 " de tous les modules disponibles localement",
                                 message=["\x03\x02%s\x03\x02 (%s)" % (im, self.srv.context.modules[im].help_tiny ()) for im in self.srv.context.modules if hasattr(self.srv.context.modules[im], "help_tiny")])
          return res

      elif self.cmd[0] == "more":
          if self.channel == self.srv.nick:
              if self.sender in self.srv.moremessages:
                  return self.srv.moremessages[self.sender]
          else:
              if self.channel in self.srv.moremessages:
                  return self.srv.moremessages[self.channel]

      elif self.cmd[0] == "dcc":
        print("dcctest for", self.sender)
        self.srv.send_dcc("Hello %s!" % self.nick, self.sender)
      elif self.cmd[0] == "pvdcctest":
        print("dcctest")
        return Response(self.sender, message="Test DCC")
      elif self.cmd[0] == "dccsendtest":
        print("dccsendtest")
        conn = DCC(self.srv, self.sender)
        conn.send_file("bot_sample.xml")
      else:
          return self.srv.context.treat_cmd(self)

    else:
        res = self.srv.context.treat_answer(self)
        # Assume the message starts with nemubot:
        if res is None and self.private:
            return self.srv.context.treat_ask(self)
        return res

#  def parseOwnerCmd(self, cmd):


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
