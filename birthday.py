# coding=utf-8

import counter
from datetime import datetime

BIRTHDAYS = list()

def xmlparse(node):
  for item in node.getElementsByTagName("item"):
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

    BIRTHDAYS.append((item.getAttribute("name"), datetime(year, month, day, hour, minute, second)))

def xmlsave(doc):
  top = doc.createTextNode("birthday")
  for brth in BIRTHDAYS:
    item = doc.createTextNode("item")
    item.setAttribute("", "")
    top.appendChild(item);
  
def parseanswer(s, channel, sender, cmd):
  if len(cmd) < 2 or cmd[1].lower() == "moi":
    name = sender.lower()
  else:
    name = cmd[1].lower()

  matches = []

  if name in birthdays:
    matches.append(name)
  else:
    for k in birthdays.keys():
      if k.find(name) == 0:
        matches.append(k)

  if len(matches) == 1:
    (n, d) = (matches[0], birthdays[matches[0]])
    tyd = d
    tyd = datetime(date.today().year, tyd.month, tyd.day)

    if tyd.day == datetime.today().day and tyd.month == datetime.today().month:
      newyear.launch (s, info[2], d, ["", "C'est aujourd'hui l'anniversaire de %s ! Il a%s. Joyeux anniversaire :)" % (n, "%s")], cmd)
    else:
      if tyd < datetime.today():
        tyd = datetime(date.today().year + 1, tyd.month, tyd.day)

      newyear.launch (s, info[2], tyd, ["Il reste%s avant l'anniversaire de %s !" % ("%s", n), ""], cmd)
  else:
    s.send("PRIVMSG %s :%s: désolé, je ne connais pas la date d'anniversaire de %s. Quand est-il né ?\r\n"%(info[2], sender[0], name))


def parseask(s, channel, sender, msgl):
  if re.match(".*(date de naissance|birthday|geburtstag|née?|nee? le|born on).*", msgl) is not None:
    result = re.match("[^0-9]+(([0-9]{1,4})[^0-9]+([0-9]{1,2}|janvier|january|fevrier|février|february|mars|march|avril|april|mai|maï|may|juin|juni|juillet|july|jully|august|aout|août|septembre|september|october|obtobre|novembre|november|decembre|décembre|december)([^0-9]+([0-9]{1,4}))?)[^0-9]+(([0-9]{1,2})[^0-9]*[h':][^0-9]*([0-9]{1,2}))?.*", msgl)
    if result is None:
      s.send("PRIVMSG %s :%s: je ne reconnais pas le format de ta date de naissance :(\r\n"%(channel, sender))
    else:
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
        minute = result.group(8)

        print "Chaîne reconnue : %s/%s/%s %s:%s"%(day, month, year, hour, minute)
        if year == None:
          year = date.today().year
        if hour == None:
          hour = 0
        if minute == None:
          minute = 0

        try:
          newdate = datetime(int(year), int(month), int(day), int(hour), int(minute))
          birthdays[sender[0].lower()] = newdate
          s.send("PRIVMSG %s :%s: ok, c'est noté, ta date de naissance est le %s\r\n"%(channel, sender, newdate.strftime("%A %d %B %Y à %H:%M")))
        except ValueError:
          s.send("PRIVMSG %s :%s: ta date de naissance me paraît peu probable...\r\n"%(channel, sender))
    return True
  return False
