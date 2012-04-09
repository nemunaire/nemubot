# coding=utf-8

import re
import time
from datetime import timedelta
from datetime import datetime
from datetime import date
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation

filename = ""
channels = "#nemutest #42sh #epitagueule"
MANCHE = None
SCORES = dict ()
temps = dict ()

def xmlparse(node):
  """Parse the given node and add scores to the global list."""
  global SCORES, MANCHE
  for item in node.getElementsByTagName("score"):
    SCORES[item.getAttribute("name")] = (int(item.getAttribute("fourtytwo")),
                                         int(item.getAttribute("twentythree")),
                                         int(item.getAttribute("pi")),
                                         int(item.getAttribute("notfound")),
                                         int(item.getAttribute("tententen")),
                                         int(item.getAttribute("leet")),
                                         int(item.getAttribute("great")),
                                         int(item.getAttribute("bad")))
  manche = node.getElementsByTagName("manche")[0]
  MANCHE = (int(manche.getAttribute("number")),
            manche.getAttribute("winner"),
            int(manche.getAttribute("winner_score")),
            manche.getAttribute("who"),
#            datetime.now ())
            datetime.fromtimestamp (time.mktime (time.strptime (manche.getAttribute("date")[:19], "%Y-%m-%d %H:%M:%S"))))

def load_module(datas_path):
  """Load this module"""
  global MANCHE, SCORES, filename
  MANCHE = None
  SCORES = dict ()
  filename = datas_path + "/42.xml"

  print ("Loading 42scores ...",)
  dom = parse(filename)
  xmlparse (dom.documentElement)
  print ("done (%d loaded, currently in round %d)" % (len(SCORES), -42))

def save_module():
  """Save the dates"""
  global filename
  print ("Saving birthdays ...",)

  impl = getDOMImplementation()
  newdoc = impl.createDocument(None, 'game', None)
  top = newdoc.documentElement

  for name in SCORES.keys():
    scr = 'fourtytwo="%d" twentythree="%d" pi="%d" notfound="%d" tententen="%d" leet="%d" great="%d" bad="%d"'% SCORES[name]
    item = parseString ('<score name="%s" %s />' % (name, scr)).documentElement
    top.appendChild(item);

  top.appendChild(parseString ('<manche number="%d" winner="%s" winner_score="%d" who="%s" date="%s" />' % MANCHE).documentElement)

  with open(filename, "w") as f:
    newdoc.writexml (f)
  print ("done")


def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "!42: display scores\n!42 help: display the performed calculate\n!42 manche: display information about current round\n!42 /who/: show the /who/'s scores"

def help_full ():
  return "!anniv /who/: gives the remaining time before the anniversary of /who/\nIf /who/ is not given, gives the remaining time before your anniversary.\n\n To set yout birthday, say it to nemubot :)"


def rev (tupl):
  (k, v) = tupl
  return (v, k)

def parseanswer (msg):
  if msg.cmd[0] == "42" or msg.cmd[0] == "score" or msg.cmd[0] == "scores":
    global SCORES, MANCHE
    if len(msg.cmd) > 1 and (msg.cmd[1] == "help" or msg.cmd[1] == "aide"):
      msg.send_chn ("Formule : normal * 2 - bad * 10 + great * 5 + leet * 3 + pi * 3.1415 + dt + not_found * 4.04")
    elif len(msg.cmd) > 1 and (msg.cmd[1] == "manche" or msg.cmd[1] == "round"):
      msg.send_chn ("Nous sommes dans la %de manche, gagnée par %s avec %d points et commencée par %s le %s"%MANCHE)
  #elif where == "#nemutest":
    else:
      phrase = ""

      if len(msg.cmd) > 1:
        if msg.cmd[1].lower() in SCORES:
          (normal, bad, great, leet, pi, dt, nf) = user(msg.cmd[1])
          phrase += " %s: 42: %d, 23: %d, bad: %d, great: %d, leet: %d, pi: %d, 404: %d = %d."%(msg.cmd[1], normal, dt, bad, great, leet, pi, nf, normal * 2 - bad * 10 + great * 5 + leet * 3 + pi * 3.1415 + dt + nf * 4.04)
        else:
          phrase = " %s n'a encore jamais joué,"%(msg.cmd[1])
      else:
        joueurs = dict()
#      for player in players:
        for player in SCORES.keys():
          if player in SCORES:
            joueurs[player] = score(player)

        for nom, scr in sorted(joueurs.items(), key=rev, reverse=True):
          if phrase == "":
            phrase = " *%s: %d*,"%(nom, scr)
          else:
            phrase += " %s: %d,"%(nom, scr)

      msg.send_chn ("Scores :%s" % (phrase[0:len(phrase)-1]))
    return True
  else:
    return False


def score(who):
  (qd, dt, pi, nf, ttt, leet, great, bad) = user(who)
#  return (normal * 2 + leet * 3 + pi * 3.1415 + dt + nf * 4.04) * (10000 * great / (1 + bad * 2.5))
  return (qd * 2 - bad * 10 + great * 5 + leet * 3 + pi * 3.1415 + dt + nf * 4.04)


def win(s, who):
  global SCORES, MANCHE
  who = who.lower()

  (num_manche, winner, nb_points, whosef, dayte) = MANCHE

  maxi_scor = 0
  maxi_name = None

  for player in SCORES.keys():
    scr = score(player)
    if scr > maxi_scor:
      maxi_scor = scr
      maxi_name = player

  #Reset !
  SCORES = dict()
#  SCORES[maxi_name] = (-10, 0, -4, 0, 0, -2, 0)
#  SCORES[maxi_name] = (0, 0, 0, 0, 0, 0, 0)
  SCORES[who] = (0, 0, 1, 1, 0, 1, -1, -4)

  if who != maxi_name:
    msg.send_global ("Félicitations %s, tu remportes cette manche terminée par %s, avec un score de %d !"%(maxi_name, who, maxi_scor))
  else:
    msg.send_global ("Félicitations %s, tu remportes cette manche avec %d points !"%(maxi_name, maxi_scor))

  MANCHE = (num_manche + 1, maxi_name, maxi_scor, who, datetime.now ())

  print ("Nouvelle manche :", MANCHE)
  save_module ()


def user(who):
  who = who.lower()
  if who in SCORES:
    return SCORES[who]
  else:
    return (0, 0, 0, 0, 0, 0, 0, 0)


def canPlay(who):
  who = who.lower()
  if not who in temps or (temps[who].minute != datetime.now().minute or temps[who].hour != datetime.now().hour or temps[who].day != datetime.now().day):
    temps[who] = datetime.now()
    return True
  else:
    return False


def parseask (msg):
  return False

def parselisten (msg):
#  if msg.channel == "#nemutest":
  if msg.channel != "#nemutest":
    (qd, dt, pi, nf, ttt, leet, great, bad) = user(msg.sender)
    sum = qd + dt + pi + nf + ttt + leet + great + bad

    if (msg.content.strip().startswith("42") and len (msg.content) < 5) or ((msg.content.strip().lower().startswith("quarante-deux") or msg.content.strip().lower().startswith("quarante deux")) and len (msg.content) < 17):
      if datetime.now().minute == 10 and datetime.now().second == 10 and datetime.now().hour == 10:
        ttt += 1
        great += 1
      elif datetime.now().minute == 42:
        if datetime.now().second == 0:
          great += 1
        qd += 1
      else:
        bad += 1

    if (msg.content.strip().startswith("23") and len (msg.content) < 5) or ((msg.content.strip().lower().startswith("vingt-trois") or msg.content.strip().lower().startswith("vingt trois")) and len (msg.content) < 14):
      if datetime.now().minute == 23:
        if datetime.now().second == 0:
          great += 1
        dt += 1
      else:
        bad += 1

    if (msg.content.strip().startswith("101010") and len (msg.content) < 9):
      if datetime.now().minute == 10 and datetime.now().hour == 10:
        if datetime.now().second == 10:
          great += 1
        ttt += 1
      else:
        bad += 1

    if (msg.content.strip().startswith("12345") and len (msg.content) < 8) or (msg.content.strip().startswith("012345") and len (msg.content) < 9):
      if datetime.now().hour == 1 and datetime.now().minute == 23 and datetime.now().second == 45:
        great += 1
        dt += 1
      else:
        bad += 1

    if len (msg.content) < 12 and (msg.content.strip().lower().startswith("leet time") or msg.content.strip().lower().startswith("leettime") or msg.content.strip().lower().startswith("l33t time") or msg.content.strip().lower().startswith("1337")):
      if datetime.now().hour == 13 and datetime.now().minute == 37:
        if datetime.now().second == 0:
          great += 1
        leet += 1
      else:
        bad += 1

    if len (msg.content) < 11 and (msg.content.strip().lower().startswith("pi time") or msg.content.strip().lower().startswith("pitime") or msg.content.strip().lower().startswith("3.14 time")):
      if datetime.now().hour == 3 and datetime.now().minute == 14:
        if datetime.now().second == 15 or datetime.now().second == 16:
          great += 1
        pi += 1
      else:
        bad += 1

    if len (msg.content) < 16 and (msg.content.strip().lower().startswith("time not found") or msg.content.strip().lower().startswith("timenotfound") or msg.content.strip().lower().startswith("404 time")) or (len (msg.content) < 6 and msg.content.strip().lower().startswith("404")):
      if datetime.now().hour == 4 and datetime.now().minute == 4:
        if datetime.now().second == 0 or datetime.now().second == 4:
          great += 1
        nf += 1
      else:
        bad += 1

    if sum != qd + dt + pi + nf + ttt + leet + great + bad and (canPlay (msg.sender) or (datetime.now().second == 45 and datetime.now().minute == 23 and datetime.now().hour == 1)):
      SCORES[msg.sender.lower()] = (qd, dt, pi, nf, ttt, leet, great, bad)
      if great >= 42:
        print ("Nous avons un vainqueur ! Nouvelle manche :p")
        win(s, msg.sender)
      else:
        save_module ()
  return False
