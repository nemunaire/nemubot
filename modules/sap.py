# coding=utf-8

"""Find information about an SAP transaction codes"""

import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

nemubotversion = 4.0

from nemubot.module.more import Response


def help_full():
    return "Retrieve SAP transaction codes and details using tcodes or keywords: !tcode <transaction code|keywords>"


@hook.command("tcode")
def cmd_tcode(msg):
    if not len(msg.args):
        raise IMException("indicate a transaction code or "
                           "a keyword to search!")

    url = ("http://www.tcodesearch.com/tcodes/search?q=%s" %
           urllib.parse.quote(msg.args[0]))

    page = web.getURLContent(url)
    soup = BeautifulSoup(page)

    res = Response(channel=msg.channel,
                   nomore="No more transaction code",
                   count=" (%d more tcodes)")


    search_res = soup.find("", {'id':'searchresults'})
    for item in search_res.find_all('dd'):
        res.append_message(item.get_text().split('\n')[1].strip())

    return res
