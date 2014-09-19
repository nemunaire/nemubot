# coding=utf-8

"""Use MediaWiki API to get pages"""

import json
import re
import urllib.parse
import urllib.request

from hooks import hook
from tools.web import striphtml

nemubotversion = 3.4

def get_raw_page(site, term, ssl=False):
    # Built IRL
    url = "http%s://%s/w/api.php?format=json&redirects&action=query&prop=revisions&rvprop=content&titles=%s" % (
        "s" if ssl else "", site, urllib.parse.quote(term))
    print_debug(url)

    # Make the request
    raw = urllib.request.urlopen(url)
    data = json.loads(raw.read().decode())

    for k in data["query"]["pages"]:
        try:
            return data["query"]["pages"][k]["revisions"][0]["*"]
        except:
            raise IRCException("article not found")

def get_unwikitextified(site, wikitext, ssl=False):
    # Built IRL
    url = "http%s://%s/w/api.php?format=json&action=expandtemplates&text=%s" % (
        "s" if ssl else "", site, urllib.parse.quote(wikitext))
    print_debug(url)

    # Make the request
    raw = urllib.request.urlopen(url)
    data = json.loads(raw.read().decode())

    return data["expandtemplates"]["*"]


def strip_model(cnt):
    # Strip models at begin and end: mostly useless
    cnt = re.sub(r"^(({{([^{]|\s|({{(.|\s|{{.*?}})*?}})*?)*?}}|\[\[(.|\s|\[\[.*?\]\])*?\]\])\s*)+", "", cnt)
    #cnt = re.sub(r"({{([^{]|\s|({{(.|\s|{{.*?}})*?}})*?)*?}}\s?)+$", "", cnt)

    # Strip HTML comments
    cnt = re.sub(r"<!--.*?-->", "", cnt)

    # Strip ref
    cnt = re.sub(r"<ref.*?/ref>", "", cnt)
    return cnt

def parse_wikitext(site, cnt, ssl=False):
    for i,_,_,_ in re.findall(r"({{([^{]|\s|({{(.|\s|{{.*?}})*?}})*?)*?}})", cnt):
        cnt = cnt.replace(i, get_unwikitextified(site, i, ssl), 1)

    # Strip [[...]]
    cnt, _ = re.subn(r"\[\[([^]]*\|)?([^]]*?)\]\]", r"\2", cnt)

    # Strip HTML tags
    cnt = striphtml(cnt)

    return cnt

def irc_format(cnt):
    cnt, _ = re.subn(r"(?P<title>==+)\s*(.*?)\s*(?P=title)\n*", "\x03\x16" + r"\2" + " :\x03\x16 ", cnt)
    return cnt.replace("'''", "\x03\x02").replace("''", "\x03\x1f")

def get_page(site, term, ssl=False):
    return strip_model(get_raw_page(site, term, ssl))


@hook("in_PRIVMSG_cmd", "mediawiki")
def cmd_mediawiki(msg):
    """Read an article on a MediaWiki"""
    if len(msg.cmds) < 3:
        raise IRCException("indicate a domain and a term to search")

    return Response(get_page(msg.cmds[1], " ".join(msg.cmds[2:])),
                    channel=msg.receivers)


@hook("in_PRIVMSG_cmd", "wikipedia")
def cmd_wikipedia(msg):
    if len(msg.cmds) < 3:
        raise IRCException("indicate a lang and a term to search")

    site = msg.cmds[1] + ".wikipedia.org"

    return Response(get_page(site, " ".join(msg.cmds[2:])),
                    line_treat=lambda line: irc_format(parse_wikitext(site, line)),
                    channel=msg.receivers)
