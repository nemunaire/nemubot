# coding=utf-8
from datetime import date
from datetime import datetime
from datetime import timedelta

channels = "#nemutest #42sh #epitagueule"

manche = (2, 'maxence23', datetime(2012, 3, 7, 22, 23, 0, 0), "colona", 193)

#score42 = {'nemunaire': (46, 5, 19, 1, 1, 27), 'cocacompany': (1, 0, 0, 0, 0, 0), 'nelson': (5, 5, 0, 0, 0, 1), 'xetal': (10, 2, 0, 0, 0, 2), 'colona': (31, 4, 32, 0, 1, 13), 'bob': (47, 4, 19, 0, 1, 27), 'benf': (12, 8, 0, 0, 1, 2), 'maxence23': (46, 18, 42, 1, 1, 45)}
score42 = {'nemunaire': (49, 1, 40, 2, 2, 42, 2), 'xetal': (1, 0, 0, 0, 0, 0, 0), 'benf': (3, 0, 0, 0, 0, 0, 0), 'colona': (23, 0, 9, 0, 1, 18, 0), 'nelson': (7, 0, 0, 0, 0, 3, 0), 'maxence23': (43, -4, 25, 1, 1, 37, 0), 'bob': (39, 1, 14, 1, 0, 26, 0), 'cccompany': (1, 0, 0, 0, 0, 1, 0)}

temps = dict()

def scores(s, cmd, where):
  global score42
  if len(cmd) > 1 and (cmd[1] == "help" or cmd[1] == "aide"):
    s.send("PRIVMSG %s :Formule : normal * 2 - bad * 10 + great * 5 + leet * 3 + pi * 3.1415 + dt + not_found * 4.04\r\n"%(where))
  elif len(cmd) > 1 and (cmd[1] == "manche"):
    txt = "Nous sommes dans la %de manche, commencée par %s le %s et gagnée par %s avec %d points"%manche
    s.send("PRIVMSG %s :%s\r\n"%(where, txt))
  #elif where == "#nemutest":
  else:
    phrase = ""
    if where == "#42sh":
      players = ["Bob", "colona", "maxence23", "nemunaire", "Xetal"]
    elif where == "#tc":
      players = ["benf", "Bob", "maxence23", "nemunaire", "Xetal"]
    elif where == "#epitagueule":
      players = ["benf", "Bob", "colona", "cccompany", "maxence23", "nelson", "nemunaire", "Xetal"]
    else:
      players = score42.keys()

    if len(cmd) > 1:
      if cmd[1].lower() in score42:
        (normal, bad, great, leet, pi, dt, nf) = user(cmd[1])
        phrase += " %s: 42: %d, 23: %d, bad: %d, great: %d, leet: %d, pi: %d, 404: %d = %d."%(cmd[1], normal, dt, bad, great, leet, pi, nf, normal * 2 - bad * 10 + great * 5 + leet * 3 + pi * 3.1415 + dt + nf * 4.04)
      else:
        phrase = " %s n'a encore jamais joué,"%(cmd[1])
    else:
      joueurs = dict()
#      for player in players:
      for player in score42.keys():
        if player in score42:
          joueurs[player] = score(player)

      for nom, scr in sorted(joueurs.iteritems(), key=lambda (k,v): (v,k), reverse=True):
        if phrase == "":
          phrase = " *%s: %d*,"%(nom, scr)
        else:
          phrase += " %s: %d,"%(nom, scr)

    s.send("PRIVMSG %s :Scores :%s\r\n"%(where, phrase[0:len(phrase)-1]))


def score(who):
  (normal, bad, great, leet, pi, dt, nf) = user(who)
#  return (normal * 2 + leet * 3 + pi * 3.1415 + dt + nf * 4.04) * (10000 * great / (1 + bad * 2.5))
  return (normal * 2 - bad * 10 + great * 5 + leet * 3 + pi * 3.1415 + dt + nf * 4.04)
  

def win(s, who):
  global score42, manche
  who = who.lower()

  (num_manche, whosef, dayte, winner, nb_points) = manche

  maxi_scor = 0
  maxi_name = None

  for player in score42.keys():
    scr = score(player)
    if scr > maxi_scor:
      maxi_scor = scr
      maxi_name = player

  #Reset !
  score42 = dict()
#  score42[maxi_name] = (-10, 0, -4, 0, 0, -2, 0)
  score42[maxi_name] = (0, 0, 0, 0, 0, 0, 0)
  score42[who] = (0, -4, -1, 1, 1, 1, 0)

  for chan in channels.split(' '):
    if who != maxi_name:
      s.send("PRIVMSG %s :Félicitations %s, tu remportes cette manche terminée par %s, avec un score de %d !\r\n"%(chan, maxi_name, who, maxi_scor))
    else:
      s.send("PRIVMSG %s :Félicitations %s, tu remportes cette manche avec %d points !\r\n"%(chan, maxi_name, maxi_scor))

  manche = (num_manche + 1, who, datetime.now(), maxi_name, maxi_scor)

  print "Nouvelle manche :", manche
  print datetime.now(), score42
    

def user(who):
  who = who.lower()
  if who in score42:
    return score42[who]
  else:
    return (0, 0, 0, 0, 0, 0, 0)


def canPlay(who):
  who = who.lower()
  if not who in temps or (temps[who].minute != datetime.now().minute or temps[who].hour != datetime.now().hour or temps[who].day != datetime.now().day):
    temps[who] = datetime.now()
    return True
  else:
    return False


def go(s, sender, msgpart, where):
  if where != "#nemutest":
    great = 0

    if (msgpart.strip().startswith("42") and len (msgpart) < 5) or ((msgpart.strip().lower().startswith("quarante-deux") or msgpart.strip().lower().startswith("quarante deux")) and len (msgpart) < 17):
      (normal, bad, great, leet, pi, dt, nf) = user(sender[0])
      if canPlay(sender[0]):
        if datetime.now().minute == 42:
          if datetime.now().second == 0:
            great += 1
          normal += 1
        else:
          bad += 1
        score42[sender[0].lower()] = (normal, bad, great, leet, pi, dt, nf)
        print datetime.now(), score42

    if (msgpart.strip().startswith("23") and len (msgpart) < 5) or ((msgpart.strip().lower().startswith("vingt-trois") or msgpart.strip().lower().startswith("vingt trois")) and len (msgpart) < 14):
      (normal, bad, great, leet, pi, dt, nf) = user(sender[0])
      if canPlay(sender[0]):
        if datetime.now().minute == 23:
          if datetime.now().second == 0:
            great += 1
          dt += 1
        else:
          bad += 1
        score42[sender[0].lower()] = (normal, bad, great, leet, pi, dt, nf)
        print datetime.now(), score42

    if len (msgpart) < 12 and (msgpart.strip().lower().startswith("leet time") or msgpart.strip().lower().startswith("leettime") or msgpart.strip().lower().startswith("l33t time") or msgpart.strip().lower().startswith("1337")):
      (normal, bad, great, leet, pi, dt, nf) = user(sender[0])
      if canPlay(sender[0]):
        if datetime.now().hour == 13 and datetime.now().minute == 37:
          if datetime.now().second == 0:
            great += 1
          leet += 1
        else:
          bad += 1
        score42[sender[0].lower()] = (normal, bad, great, leet, pi, dt, nf)
        print datetime.now(), score42

    if len (msgpart) < 11 and (msgpart.strip().lower().startswith("pi time") or msgpart.strip().lower().startswith("pitime") or msgpart.strip().lower().startswith("3.14 time")):
      (normal, bad, great, leet, pi, dt, nf) = user(sender[0])
      if canPlay(sender[0]):
        if datetime.now().hour == 3 and datetime.now().minute == 14:
          if datetime.now().second == 15 or datetime.now().second == 16:
            great += 1
          pi += 1
        else:
          bad += 1
        score42[sender[0].lower()] = (normal, bad, great, leet, pi, dt, nf)
        print datetime.now(), score42

    if len (msgpart) < 16 and (msgpart.strip().lower().startswith("time not found") or msgpart.strip().lower().startswith("timenotfound") or msgpart.strip().lower().startswith("404 time")) or (len (msgpart) < 6 and msgpart.strip().lower().startswith("404")):
      (normal, bad, great, leet, pi, dt, nf) = user(sender[0])
      if canPlay(sender[0]):
        if datetime.now().hour == 4 and datetime.now().minute == 04:
          if datetime.now().second == 0 or datetime.now().second == 4:
            great += 1
          nf += 1
        else:
          bad += 1
        score42[sender[0].lower()] = (normal, bad, great, leet, pi, dt, nf)
        print datetime.now(), score42

    if great >= 42:
      print "Nous avons un vainqueur ! Nouvelle manche :p"
      win(s, sender[0])
