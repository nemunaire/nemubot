# coding=utf-8

import urllib.request
import json
import re
from tools import web
from tools.web import striphtml

nemubotversion = 3.3

def help_tiny ():
  return "Find information about an SAP transaction codes"

def help_full ():
  return "!tcode <transaction code|keywords>"

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_tcode, "tcode"))


def cmd_tcode(msg):
  if len(msg.cmds) != 2:
      raise IRCException("indicate a transaction code or a keyword to search!")

  url = "http://www.tcodesearch.com/tcodes/search?q=%s" % urllib.parse.quote(msg.cmds[1])
  page = web.getURLContent(url)

  res =  Response(msg.sender, channel=msg.channel,
                  nomore="No more transaction code", count=" (%d more tcodes)")

  if page is not None:
    index = page.index('<div id="searchresults">') + len('<div id="searchresults">')
    end = page[index:].index('</div>')+index
    strscope = page[index:end]
    for tcode in re.finditer('<strong> ([a-zA-Z0-9_]*)</strong> - ([^\n]*)\n', strscope):
      res.append_message("\x02%s\x0F - %s" % (tcode.group(1), striphtml(tcode.group(2))))

  return res
