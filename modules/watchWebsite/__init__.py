# coding=utf-8

from datetime import datetime
from datetime import timedelta
import http.client
import hashlib
import re
import socket
import sys
import urllib.parse
from urllib.parse import urlparse
from urllib.request import urlopen

from .atom import Atom

nemubotversion = 3.3

def help_tiny ():
  """Line inserted in the response to the command !help"""
  return "Alert on changes on websites"

def help_full ():
  return "This module is autonomous you can't interract with it."

def load(context):
    """Register watched website"""
    DATAS.setIndex("url", "watch")
    for site in DATAS.getNodes("watch"):
        start_watching(site)

def unload(context):
    """Unregister watched website"""
    # Useless in 3.3?
#    for site in DATAS.getNodes("watch"):
#        context.del_event(site["evt_id"])
    pass

def getPageContent(url):
    """Returns the content of the given url"""
    print_debug("Get page %s" % url)
    raw = urlopen(url, timeout=15)
    return raw.read().decode()

def start_watching(site):
    o = urlparse(site["url"], "http")
    print_debug("Add event for site: %s" % o.netloc)
    evt = ModuleEvent(func=getPageContent, cmp_data=site["lastcontent"],
                      func_data=site["url"],
                      intervalle=site.getInt("time"),
                      call=alert_change, call_data=site)
    site["_evt_id"] = add_event(evt)


def del_site(msg):
    if len(msg.cmds) <= 1:
        return Response(msg.sender, "quel site dois-je arrêter de surveiller ?",
                        msg.channel, msg.nick)

    url = msg.cmds[1]

    o = urlparse(url, "http")
    if o.scheme != "" and url in DATAS.index:
        site = DATAS.index[url]
        for a in site.getNodes("alert"):
            if a["channel"] == msg.channel:
                if (msg.sender == a["sender"] or msg.is_owner):
                    site.delChild(a)
                    if not site.hasNode("alert"):
                      del_event(site["_evt_id"])
                      DATAS.delChild(site)
                    save()
                    return Response(msg.sender,
                                   "je ne surveille désormais plus cette URL.",
                                   channel=msg.channel, nick=msg.nick)
                else:
                  return Response(msg.sender,
                                  "Vous ne pouvez pas supprimer cette URL.",
                                  channel=msg.channel, nick=msg.nick)
        return Response(msg.sender,
                        "je ne surveillais pas cette URL, impossible de la supprimer.",
                        channel=msg.channel, nick=msg.nick)
    return Response(msg.sender, "je ne surveillais pas cette URL pour vous.",
                    channel=msg.channel, nick=msg.nick)

def add_site(msg):
    if len(msg.cmds) <= 1:
        return Response(msg.sender, "quel site dois-je surveiller ?",
                        msg.channel, msg.nick)

    url = msg.cmds[1]

    o = urlparse(url, "http")
    if o.netloc != "":
        alert = ModuleState("alert")
        alert["sender"] = msg.sender
        alert["server"] = msg.server
        alert["channel"] = msg.channel
        alert["message"] = "%s a changé !" % url

        if url not in DATAS.index:
            watch = ModuleState("watch")
            watch["type"] = "diff"
            watch["url"] = url
            watch["time"] = 123
            DATAS.addChild(watch)
            watch.addChild(alert)
            start_watching(watch)
        else:
            DATAS.index[url].addChild(alert)
    else:
        return Response(msg.sender, "je ne peux pas surveiller cette URL",
                        channel=msg.channel, nick=msg.nick)

    save()
    return Response(msg.sender, channel=msg.channel, nick=msg.nick,
                    message="ce site est maintenant sous ma surveillance.")

def format_response(site, data1='%s', data2='%s', data3='%s', data4='%s'):
    for a in site.getNodes("alert"):
        if a["message"].count("%s") == 1: data = data1
        elif a["message"].count("%s") == 2: data = (data2, data1)
        elif a["message"].count("%s") == 3: data = (data3, data2, data1)
        elif a["message"].count("%s") == 4: data = (data4, data3, data2, data1)
        else: data = ()
        send_response(a["server"], Response(a["sender"], a["message"] % data,
                                     channel=a["channel"], server=a["server"]))

def alert_change(content, site):
    """Alert when a change is detected"""
    if content is None:
        start_watching(site)
        return

    if site["type"] == "atom":
        if site["_lastpage"] is None:
            if site["lastcontent"] is None:
                site["_lastpage"] = Atom(content)
            else:
                site["_lastpage"] = Atom(site["lastcontent"])
        try:
            page = Atom(content)
        except:
            print ("An error occurs during Atom parsing. Restart event...")
            start_watching(site)
            return
        diff = site["_lastpage"].diff(page)
        if len(diff) > 0:
            site["_lastpage"] = page
            print_debug("[%s] Page differ!" % getHost(site["url"]))
            diff.reverse()
            for d in diff:
                site.setIndex("term", "category")
                categories = site.index

                if len(categories) > 0:
                    if d.category is None or d.category not in categories:
                        format_response(site, link, categories[""]["part"])
                    else:
                        format_response(site, link, categories[d.category]["part"])
                else:
                    format_response(site, link, urllib.parse.unquote(d.title))
        else:
            start_watching(site)
            return #Stop here, no changes, so don't save

    else: # Just looking for any changes
        format_response(site, site["url"])
    site["lastcontent"] = content
    start_watching(site)
    save()
