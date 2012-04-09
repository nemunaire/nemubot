# coding=utf-8

import re
from datetime import datetime
from datetime import date
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation

filename = ""
BIRTHDAYS = {}

def xmlparse(node):
  """Parse the given node and add birthdays to the global list."""
  for item in node.getElementsByTagName("birthday"):
    if (item.hasAttribute("year")):
      year = int(item.getAttribute("year"))
    else:
      year = 0
    if (item.hasAttribute("month")):
      month = int(item.getAttribute("month"))
    else:
      month = 0
    if (item.hasAttribute("day")):
      day = int(item.getAttribute("day"))
    else:
      day = 0
    if (item.hasAttribute("hour")):
      hour = int(item.getAttribute("hour"))
    else:
      hour = 0
    if (item.hasAttribute("minute")):
      minute = int(item.getAttribute("minute"))
    else:
      minute = 0
    second = 1

    BIRTHDAYS[item.getAttribute("name")] = datetime(year, month, day, hour, minute, second)


def load_module(datas_path):
  """Load this module"""
  global BIRTHDAYS, filename
  BIRTHDAYS = {}
  filename = datas_path + "/birthdays.xml"

  print ("Loading birthdays ...",)
  dom = parse(filename)
  xmlparse (dom.getElementsByTagName('birthdays')[0])
  print ("done (%d loaded)" % len(BIRTHDAYS))


def save_module():
  """Save the dates"""
  global filename
  print ("Saving birthdays ...",)

  impl = getDOMImplementation()
  newdoc = impl.createDocument(None, 'birthdays', None)
  top = newdoc.documentElement

  for name in BIRTHDAYS.keys():
    day = BIRTHDAYS[name]
    bonus=""
    if day.hour != 0:
      bonus += 'hour="%s" ' % day.hour
    if day.minute != 0:
      bonus += 'minute="%s" ' % day.minute
    item = parseString ('<birthday name="%s" year="%d" month="%d" day="%d" %s />' % (name, day.year, day.month, day.day, bonus)).documentElement
    top.appendChild(item);

  with open(filename, "w") as f:
    newdoc.writexml (f)
  print ("done")


def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "!anniv /who/: gives the remaining time before the anniversary of /who/"


def help_full ():
  return "!anniv /who/: gives the remaining time before the anniversary of /who/\nIf /who/ is not given, gives the remaining time before your anniversary.\n\n To set yout birthday, say it to nemubot :)"


def parseanswer(msg):
  if msg.cmd[0] == "anniv":
    if len(msg.cmd) < 2 or msg.cmd[1].lower() == "moi" or msg.cmd[1].lower() == "me":
      name = msg.sender.lower()
    else:
      name = msg.cmd[1].lower()

    matches = []

    if name in BIRTHDAYS:
      matches.append(name)
    else:
      for k in BIRTHDAYS.keys ():
        if k.find (name) == 0:
          matches.append (k)

    if len(matches) == 1:
      (n, d) = (matches[0], BIRTHDAYS[matches[0]])
      tyd = d
      tyd = datetime(date.today().year, tyd.month, tyd.day)

      if tyd.day == datetime.today().day and tyd.month == datetime.today().month:
        msg.send_chn (msg.countdown_format (d, "", "C'est aujourd'hui l'anniversaire de %s ! Il a%s. Joyeux anniversaire :)" % (n, "%s")))
      else:
        if tyd < datetime.today():
          tyd = datetime(date.today().year + 1, tyd.month, tyd.day)

        msg.send_chn (msg.countdown_format (tyd, "Il reste%s avant l'anniversaire de %s !" % ("%s", n), ""))
    else:
      msg.send_chn ("%s: désolé, je ne connais pas la date d'anniversaire de %s. Quand est-il né ?"%(msg.sender, name))
    return True
  else:
    return False


def parseask(msg):
  msgl = msg.content.lower ()
  if re.match("^.*(date de naissance|birthday|geburtstag|née?|nee? le|born on).*$", msgl) is not None:
    extDate = msg.extractDate ()
    if extDate is None:
      msg.send_chn ("%s: ta date de naissance ne paraît pas valide..." % (msg.sender))
    else:
      BIRTHDAYS[msg.sender.lower()] = extDate
      msg.send_chn ("%s: ok, c'est noté, ta date de naissance est le %s" % (msg.sender, extDate.strftime("%A %d %B %Y à %H:%M")))
      save_module ()
    return True
  return False

def parselisten (msg):
  return False
