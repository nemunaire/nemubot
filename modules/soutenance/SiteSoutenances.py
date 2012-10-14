# coding=utf-8

from datetime import datetime
from datetime import timedelta
import http.client
import re
import threading
import time

from response import Response

from .Soutenance import Soutenance

class SiteSoutenances(threading.Thread):
    def __init__(self, datas):
        self.souts = list()
        self.updated = datetime.now()
        self.datas = datas
        threading.Thread.__init__(self)

    def getPage(self):
        conn = http.client.HTTPSConnection(CONF.getNode("server")["ip"], timeout=10)
        try:
            conn.request("GET", CONF.getNode("server")["url"])

            res = conn.getresponse()
            page = res.read()
        except:
            print ("[%s] impossible de récupérer la page %s."%(s, p))
            return ""
        conn.close()
        return page

    def parsePage(self, page):
        save = False
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

    def gen_response(self, req, msg):
        """Generate a text response on right server and channel"""
        return Response(req["sender"], msg, req["channel"], server=req["server"])

    def res_next(self, req):
        soutenance = self.findLast()
        if soutenance is None:
            return self.gen_response(req, "Il ne semble pas y avoir de soutenance pour le moment.")
        else:
            if soutenance.start > soutenance.hour:
                avre = "%s de *retard*"%msg.just_countdown(soutenance.start - soutenance.hour, 4)
            else:
                avre = "%s *d'avance*"%msg.just_countdown(soutenance.hour - soutenance.start, 4)
            self.gen_response(req, "Actuellement à la soutenance numéro %d, commencée il y a %s avec %s."%(soutenance.rank, msg.just_countdown(datetime.now () - soutenance.start, 4), avre))

    def res_assistants(self, req):
        assistants = self.findAssistants()
        if len(assistants) > 0:
            return self.gen_response(req, "Les %d assistants faisant passer les soutenances sont : %s." % (len(assistants), ', '.join(assistants.keys())))
        else:
            return self.gen_response(req, "Il ne semble pas y avoir de soutenance pour le moment.")

    def res_soutenance(self, req):
        name = req["user"]

        if name == "acu" or name == "yaka" or name == "acus" or name == "yakas" or name == "assistant" or name == "assistants":
            return self.res_assistants(req)
        elif name == "next":
            return self.res_next(req)

        soutenance = self.findClose(name)
        if soutenance is None:
            return self.gen_response(req, "Pas d'horaire de soutenance pour %s."%name)
        else:
            if soutenance.state == "En cours":
                return self.gen_response(req, "%s est actuellement en soutenance avec %s. Elle était prévue à %s, position %d."%(name, soutenance.assistant, soutenance.hour, soutenance.rank))
            elif soutenance.state == "Effectue":
                return self.gen_response(req, "%s a passé sa soutenance avec %s. Elle a duré %s."%(name, soutenance.assistant, msg.just_countdown(soutenance.end - soutenance.start, 4)))
            elif soutenance.state == "Retard":
                return self.gen_response(req, "%s était en retard à sa soutenance de %s."%(name, soutenance.hour))
            else:
                last = self.findLast()
                if last is not None:
                    if soutenance.hour + (last.start - last.hour) > datetime.now ():
                        return self.gen_response(req, "Soutenance de %s : %s, position %d ; estimation du passage : dans %s."%(name, soutenance.hour, soutenance.rank, msg.just_countdown((soutenance.hour - datetime.now ()) + (last.start - last.hour))))
                    else:
                        return self.gen_response(req, "Soutenance de %s : %s, position %d ; passage imminent."%(name, soutenance.hour, soutenance.rank))
                else:
                    return self.gen_response(req, "Soutenance de %s : %s, position %d."%(name, soutenance.hour, soutenance.rank))

    def res_list(self, req):
        name = req["user"]

        souts = self.findAll(name)
        if souts is None:
            self.gen_response(req, "Pas de soutenance prévues pour %s."%name)
        else:
            first = True
            for s in souts:
                if first:
                    self.gen_response(req, "Soutenance(s) de %s : - %s (position %d) ;"%(name, s.hour, s.rank))
                    first = False
                else:
                    self.gen_response(req, "                  %s  - %s (position %d) ;"%(len(name)*' ', s.hour, s.rank))

    def run(self):
        self.parsePage(self.getPage().decode())
        res = list()
        for u in self.datas.getNodes("request"):
            res.append(self.res_soutenance(u))
        return res

    def needUpdate(self):
        if self.findLast() is not None and datetime.now () - self.updated > timedelta(minutes=2):
            return True
        elif datetime.now () - self.updated < timedelta(hours=1):
            return False
        else:
            return True

    def findAssistants(self):
        h = dict()
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
