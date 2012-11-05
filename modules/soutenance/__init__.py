# coding=utf-8

import time
import re
import threading
from datetime import date
from datetime import datetime

from . import SiteSoutenances

nemubotversion = 3.3

def help_tiny():
  """Line inserted in the response to the command !help"""
  return "EPITA ING1 defenses module"

def help_full():
  return "!soutenance: gives information about current defenses state\n!soutenance <who>: gives the date of the next defense of /who/.\n!soutenances <who>: gives all defense dates of /who/"

def load(context):
    global CONF
    SiteSoutenances.CONF = CONF

def ask_soutenance(msg):
    req = ModuleState("request")
    if len(msg.cmds) > 1:
        req.setAttribute("user", msg.cmds[1])
    else:
        req.setAttribute("user", "next")
    req.setAttribute("server", msg.server)
    req.setAttribute("channel", msg.channel)
    req.setAttribute("sender", msg.sender)

    #An instance of this module is already running?
    if not DATAS.hasAttribute("_running") or DATAS["_running"].needUpdate():
        DATAS.addChild(req)
        site = SiteSoutenances.SiteSoutenances(DATAS)
        DATAS.setAttribute("_running", site)

        res = site.run()

        for n in DATAS.getNodes("request"):
            DATAS.delChild(n)

        return res
    else:
        site = DATAS["_running"]
        return site.res_soutenance(req)
