# coding=utf-8

import re
import imp
from datetime import datetime

nemubotversion = 3.0

from . import GameUpdater
from . import QDWrapper
from . import Score

channels = "#nemutest #42sh #ykar #epitagueule"
LASTSEEN = dict ()
temps = dict ()

SCORES = None

def load():
  global DATAS, SCORES, CONF
  DATAS.setIndex("name", "player")
  SCORES = QDWrapper.QDWrapper(DATAS)
  GameUpdater.SCORES = SCORES
  GameUpdater.CONF = CONF
  GameUpdater.save = save
  GameUpdater.getUser = getUser

def reload():
  imp.reload(GameUpdater)
  imp.reload(QDWrapper)
  imp.reload(Score)


def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "42 game!"

def help_full ():
  return "!42: display scores\n!42 help: display the performed calculate\n!42 manche: display information about current round\n!42 /who/: show the /who/'s scores"


def parseanswer (msg):
  if msg.cmd[0] == "42" or msg.cmd[0] == "score" or msg.cmd[0] == "scores":
    global SCORES
    if len(msg.cmd) > 2 and msg.is_owner and ((msg.cmd[1] == "merge" and len(msg.cmd) > 3) or msg.cmd[1] == "oupstriche"):
      if msg.cmd[2] in SCORES and (len(msg.cmd) <= 3 or msg.cmd[3] in SCORES):
        if msg.cmd[1] == "merge":
          SCORES[msg.cmd[2]].merge (SCORES[msg.cmd[3]])
          del SCORES[msg.cmd[3]]
          msg.send_chn ("%s a été correctement fusionné avec %s."%(msg.cmd[3], msg.cmd[2]))
        elif msg.cmd[1] == "oupstriche":
          SCORES[msg.cmd[2]].oupsTriche()
      else:
        if msg.cmd[2] not in SCORES:
          msg.send_chn ("%s n'est pas un joueur connu."%msg.cmd[2])
        elif msg.cmd[3] not in SCORES:
          msg.send_chn ("%s n'est pas un joueur connu."%msg.cmd[3])
    elif len(msg.cmd) > 1 and (msg.cmd[1] == "help" or msg.cmd[1] == "aide"):
      msg.send_chn ("Formule : \"42\" * 2 + great * 5 + leet * 13.37 + (pi + 1) * 3.1415 * (not_found + 1) + tententen * 10 + \"23\" - (bad + 1) * 10 * (triche * 5 + 1) + 7")
    elif len(msg.cmd) > 1 and (msg.cmd[1] == "manche" or msg.cmd[1] == "round"):
      manche = DATAS.getNode("manche")
      msg.send_chn ("Nous sommes dans la %de manche, gagnée par %s avec %d points et commencée par %s le %s." % (manche.getInt("number"), manche["winner"], manche.getInt("winner_score"), manche["who"], manche.getDate("date")))
    #elif msg.channel == "#nemutest":
    else:
      phrase = ""

      if len(msg.cmd) > 1:
        if msg.cmd[1] in SCORES:
          phrase += " " + msg.cmd[1] + ": " + SCORES[msg.cmd[1]].details()
        else:
          phrase = " %s n'a encore jamais joué,"%(msg.cmd[1])
      else:
        for nom, scr in sorted(SCORES.items(), key=rev, reverse=True):
          score = scr.score()
          if score != 0:
            if phrase == "":
              phrase = " *%s.%s: %d*,"%(nom[0:1], nom[1:len(nom)], score)
            else:
              phrase += " %s.%s: %d,"%(nom[0:1], nom[1:len(nom)], score)

      msg.send_chn ("Scores :%s" % (phrase[0:len(phrase)-1]))
    return True
  else:
    return False


def win(msg):
  global SCORES
  who = msg.nick

  manche = DATAS.getNode("manche")

  maxi_scor = 0
  maxi_name = None

  for player in DATAS.index.keys():
    scr = SCORES[player].score()
    if scr > maxi_scor:
      maxi_scor = scr
      maxi_name = player

  for player in DATAS.index.keys():
    scr = SCORES[player].score()
    if scr > maxi_scor / 3:
      del SCORES[player]
    else:
      DATAS.index[player]["great"] = 0
  SCORES.flush()

  if who != maxi_name:
    msg.send_chn ("Félicitations %s, tu remportes cette manche terminée par %s, avec un score de %d !"%(maxi_name, who, maxi_scor))
  else:
    msg.send_chn ("Félicitations %s, tu remportes cette manche avec %d points !"%(maxi_name, maxi_scor))

  manche.setAttribute("number", manche.getInt("number") + 1)
  manche.setAttribute("winner", maxi_name)
  manche.setAttribute("winner_score", maxi_scor)
  manche.setAttribute("who", who)
  manche.setAttribute("date", datetime.now())

  print ("Nouvelle manche !")
  save()


def parseask (msg):
  if len(GameUpdater.DELAYED) > 0:
    if msg.nick in GameUpdater.DELAYED:
      GameUpdater.DELAYED[msg.nick].msg = msg.content
      GameUpdater.DELAYED[msg.nick].delayEvnt.set()
      return True
  return False



def rev (tupl):
  (k, v) = tupl
  return (v.score(), k)


def getUser(name):
  global SCORES
  if name not in SCORES:
    SCORES[name] = Score.Score()
  return SCORES[name]


def parselisten (msg):
  if len(GameUpdater.DELAYED) > 0 and msg.nick in GameUpdater.DELAYED and GameUpdater.DELAYED[msg.nick].good(msg.content):
    msg.send_chn("%s: n'oublie pas le nemubot: devant ta réponse pour qu'elle soit prise en compte !" % msg.nick)

  bfrseen = None
  if msg.realname in LASTSEEN:
    bfrseen = LASTSEEN[msg.realname]
  LASTSEEN[msg.realname] = datetime.now()

#  if msg.channel == "#nemutest" and msg.nick not in GameUpdater.DELAYED:
  if msg.channel != "#nemutest" and msg.nick not in GameUpdater.DELAYED:

    if re.match("^(42|quarante[- ]?deux).{,2}$", msg.content.strip().lower()):
      if msg.time.minute == 10 and msg.time.second == 10 and msg.time.hour == 10:
        getUser(msg.nick).playTen()
        getUser(msg.nick).playGreat()
      elif msg.time.minute == 42:
        if msg.time.second == 0:
          getUser(msg.nick).playGreat()
        getUser(msg.nick).playFtt()
      else:
        getUser(msg.nick).playBad()

    if re.match("^(23|vingt[ -]?trois).{,2}$", msg.content.strip().lower()):
      if msg.time.minute == 23:
        if msg.time.second == 0:
          getUser(msg.nick).playGreat()
        getUser(msg.nick).playTwt()
      else:
        getUser(msg.nick).playBad()

    if re.match("^(10){3}.{,2}$", msg.content.strip().lower()):
      if msg.time.minute == 10 and msg.time.hour == 10:
        if msg.time.second == 10:
          getUser(msg.nick).playGreat()
        getUser(msg.nick).playTen()
      else:
        getUser(msg.nick).playBad()

    if re.match("^0?12345.{,2}$", msg.content.strip().lower()):
      if msg.time.hour == 1 and msg.time.minute == 23 and (msg.time.second == 45 or (msg.time.second == 46 and msg.time.microsecond < 330000)):
        getUser(msg.nick).playSuite()
      else:
        getUser(msg.nick).playBad()

    if re.match("^[1l][e3]{2}[t7] ?t?ime.{,2}$", msg.content.strip().lower()):
      if msg.time.hour == 13 and msg.time.minute == 37:
        if msg.time.second == 0:
          getUser(msg.nick).playGreat()
        getUser(msg.nick).playLeet()
      else:
        getUser(msg.nick).playBad()

    if re.match("^(pi|3.14) ?time.{,2}$", msg.content.strip().lower()):
      if msg.time.hour == 3 and msg.time.minute == 14:
        if msg.time.second == 15 or msg.time.second == 16:
          getUser(msg.nick).playGreat()
        getUser(msg.nick).playPi()
      else:
        getUser(msg.nick).playBad()

    if re.match("^(404( ?time)?|time ?not ?found).{,2}$", msg.content.strip().lower()):
      if msg.time.hour == 4 and msg.time.minute == 4:
        if msg.time.second == 0 or msg.time.second == 4:
          getUser(msg.nick).playGreat()
        getUser(msg.nick).playNotfound()
      else:
        getUser(msg.nick).playBad()

    if getUser(msg.nick).isWinner():
      print ("Nous avons un vainqueur ! Nouvelle manche :p")
      win(msg)
      return True
    elif getUser(msg.nick).hasChanged():
      gu = GameUpdater.GameUpdater(msg, bfrseen)
      gu.start()
      return True
  return False
