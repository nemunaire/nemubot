# coding=utf-8

from datetime import datetime
from datetime import timedelta
import imp
import re
import shlex
import string
import sys
import time

from credits import Credits
import credits
dcc = __import__("DCC")
imp.reload(dcc)

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
  def __init__ (self, srv, line, private = False):
    self.srv = srv
    self.time = datetime.now ()
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
    if len(words) > 0:
      if words[0][0] == 58:
        return b' '.join(words[0:])[1:]
      else:
        return words[0]
    else:
      return ""

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


  def send_msg(self, channel, msg, cmd = "PRIVMSG", endl = "\r\n"):
    if CREDITS[self.realname].speak():
      self.srv.send_msg_verified (self.sender, channel, msg, cmd, endl)

  def send_global(self, msg, cmd = "PRIVMSG", endl = "\r\n"):
    if CREDITS[self.realname].speak():
      self.srv.send_global (msg, cmd, endl)

  def send_chn(self, msg):
    """Send msg on the same channel as receive message"""
    if (self.srv.isDCC() and self.channel == self.srv.nick) or CREDITS[self.realname].speak():
      if self.channel == self.srv.nick:
        self.send_snd (msg)
      else:
        self.srv.send_msg (self.channel, msg)

  def send_snd(self, msg):
    """Send msg to the person who send the original message"""
    if self.srv.isDCC(self.sender) or CREDITS[self.realname].speak():
      self.srv.send_msg_usr (self.sender, msg)


  def authorize(self):
    if self.srv.isDCC(self.sender):
      return True
    elif self.realname not in CREDITS:
      CREDITS[self.realname] = Credits(self.realname)
    elif self.content[0] == '`':
      return True
    elif not CREDITS[self.realname].ask():
      return False
    return self.srv.accepted_channel(self.channel)

  def treat(self, mods):
    if self.cmd == "PING":
      self.pong ()
    elif self.cmd == "PRIVMSG" and self.ctcp:
      self.parsectcp ()
    elif self.cmd == "PRIVMSG" and self.authorize():
      self.parsemsg (mods)
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


  def pong (self):
    self.srv.s.send(("PONG %s\r\n" % self.content).encode ())


  def parsectcp(self):
    if self.content == '\x01CLIENTINFO\x01':
      self.srv.send_ctcp(self.sender, "CLIENTINFO TIME USERINFO VERSION CLIENTINFO")
    elif self.content == '\x01TIME\x01':
      self.srv.send_ctcp(self.sender, "TIME %s" % (datetime.now()))
    elif self.content == '\x01USERINFO\x01':
      self.srv.send_ctcp(self.sender, "USERINFO %s" % (self.srv.realname))
    elif self.content == '\x01VERSION\x01':
      self.srv.send_ctcp(self.sender, "VERSION nemubot v3")
    elif self.content[:9] == '\x01DCC CHAT':
      words = self.content[1:len(self.content) - 1].split(' ')
      ip = self.srv.toIP(int(words[3]))
      fullname = "guest" + words[4] + words[3] +"!guest" + words[4] + words[3] + "@" + ip
      conn = dcc.DCC(self.srv, fullname)
      if conn.accept_user(ip, int(words[4])):
        self.srv.dcc_clients[conn.sender] = conn
        conn.send_dcc("Hi %s. To changes your name, say \"%s: my name is yournickname\"." % (conn.nick, self.srv.nick))
      else:
        print ("DCC: unable to connect to %s:%s" % (ip, words[4]))
    elif self.content[:7] != '\x01ACTION':
      print (self.content)
      self.srv.send_ctcp(self.sender, "ERRMSG Unknown or unimplemented CTCP request")

  def reparsemsg(self):
    if self.mods is not None:
      self.parsemsg(self.mods)
    else:
      print ("Can't reparse message")

  def parsemsg (self, mods):
    #Treat all messages starting with 'nemubot:' as distinct commands
    if self.content.find("%s:"%self.srv.nick) == 0:
      #Remove the bot name
      self.content = self.content[len(self.srv.nick)+1:].strip()
      messagel = self.content.lower()

      #Is it a simple response?
      if re.match(".*(m[' ]?entends?[ -]+tu|h?ear me|do you copy|ping)", messagel) is not None:
        self.send_chn ("%s: pong"%(self.nick))

      elif re.match(".*(quel(le)? heure est[ -]il|what time is it)", messagel) is not None:
        now = datetime.now()
        self.send_chn ("%s: j'envoie ce message à %02d:%02d:%02d."%(self.nick, now.hour, now.minute, now.second))

      elif re.match(".*di[st] (a|à) ([a-zA-Z0-9_]+) (.+)$", messagel) is not None:
        result = re.match(".*di[st] (a|à) ([a-zA-Z0-9_]+) (qu(e |'))?(.+)$", self.content)
        self.send_chn ("%s: %s"%(result.group(2), result.group(5)))
      elif re.match(".*di[st] (.+) (a|à) ([a-zA-Z0-9_]+)$", messagel) is not None:
        result = re.match(".*di[st] (.+) (à|a) ([a-zA-Z0-9_]+)$", self.content)
        self.send_chn ("%s: %s"%(result.group(3), result.group(1)))

      elif re.match(".*di[st] sur (#[a-zA-Z0-9]+) (.+)$", self.content) is not None:
        result = re.match(".*di[st] sur (#[a-zA-Z0-9]+) (.+)$", self.content)
        self.send_msg(result.group(1), result.group(2))
      elif re.match(".*di[st] (.+) sur (#[a-zA-Z0-9]+)$", self.content) is not None:
        result = re.match(".*di[st] (.+) sur (#[a-zA-Z0-9]+)$", self.content)
        self.send_msg(result.group(2), result.group(1))

      #Try modules
      else:
        for im in mods:
          if im.has_access(self) and im.parseask(self):
            return

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
      self.mods = mods
      try:
        self.cmd = shlex.split(self.content[1:])
      except ValueError:
        self.cmd = self.content[1:].split(' ')
      if self.cmd[0] == "help":
        if len (self.cmd) > 1:
          if self.cmd[1] in mods:
            try:
              self.send_snd(mods[self.cmd[1]].help_full ())
            except AttributeError:
              self.send_snd("No help for command %s" % self.cmd[1])
          else:
            self.send_snd("No help for command %s" % self.cmd[1])
        else:
          self.send_snd("Pour me demander quelque chose, commencez votre message par mon nom ; je réagis à certain messages commençant par !, consulter l'aide de chaque module :")
          for im in mods:
            try:
              self.send_snd("  - !help %s: %s" % (im.name, im.help_tiny ()))
            except AttributeError:
              continue

      elif self.cmd[0] == "dcctest":
        print("dcctest for", self.sender)
        self.srv.send_dcc("Test DCC", self.sender)
      elif self.cmd[0] == "pvdcctest":
        print("dcctest")
        self.send_snd("Test DCC")
      elif self.cmd[0] == "dccsendtest":
        print("dccsendtest")
        conn = dcc.DCC(self.srv, self.sender)
        conn.send_file("bot_sample.xml")
      else:
        for im in mods:
          if im.has_access(self) and im.parseanswer(self):
            return

    else:
      for im in mods:
        if im.has_access(self) and im.parselisten(self):
          return
      #Assume the message starts with nemubot:
      if self.private:
        for im in mods:
          if im.has_access(self) and im.parseask(self):
            return

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
