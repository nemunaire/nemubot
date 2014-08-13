# coding=utf-8

import json
import re
import urllib

nemubotversion = 3.4

from hooks import hook

def help_tiny():
    """Line inserted in the response to the command !help"""
    return "The subreddit module"

def help_full():
    return "!subreddit /subreddit/: Display information on the subreddit."

LAST_SUBS = dict()

@hook("cmd_hook", "subreddit", help="!subreddit /subreddit/: Display information on the subreddit.")
def cmd_subreddit(msg):
    global LAST_SUBS
    if len(msg.cmds) <= 1:
        if msg.channel in LAST_SUBS and len(LAST_SUBS[msg.channel]) > 0:
            subs = [LAST_SUBS[msg.channel].pop()]
        else:
            raise IRCException("Which subreddit? Need inspiration? type !horny or !bored")
    else:
        subs = msg.cmds[1:]

    all_res = list()
    for osub in subs:
        sub = re.match(r"^/?(?:(\w)/)?(\w+)/?$", osub)
        if sub is not None:
            if sub.group(1) is not None and sub.group(1) != "":
                where = sub.group(1)
            else:
                where = "r"
            try:
                req = urllib.request.Request("http://www.reddit.com/%s/%s/about.json" % (where, sub.group(2)), headers={ 'User-Agent' : "nemubot v3" })
                raw = urllib.request.urlopen(req, timeout=10)
            except urllib.error.HTTPError as e:
                raise IRCException("HTTP error occurs: %s %s" % (e.code, e.reason))
            sbr = json.loads(raw.read().decode())

            if "title" in sbr["data"]:
                res = Response(msg.sender, channel=msg.channel, nomore="No more information")
                res.append_message(("[NSFW] " if sbr["data"]["over18"] else "") + sbr["data"]["url"] + " " + sbr["data"]["title"] + ": " + sbr["data"]["public_description" if sbr["data"]["public_description"] != "" else "description"].replace("\n", " ") + " %s subscriber(s)" % sbr["data"]["subscribers"])
                if sbr["data"]["public_description"] != "":
                    res.append_message(sbr["data"]["description"].replace("\n", " "))
                all_res.append(res)
            else:
                all_res.append(Response(msg.sender, "/%s/%s doesn't exist" % (where, sub.group(2)), channel=msg.channel))
        else:
            all_res.append(Response(msg.sender, "%s is not a valid subreddit" % osub, channel=msg.channel, nick=msg.nick))

    return all_res


def parselisten(msg):
    global LAST_SUBS

    try:
        urls = re.findall("www.reddit.com(/\w/\w+/?)", msg.content)
        for url in urls:
            if msg.channel not in LAST_SUBS:
                LAST_SUBS[msg.channel] = list()
            LAST_SUBS[msg.channel].append(url)
    except:
        pass

    return False

@hook("all_post")
def parseresponse(res):
    parselisten(res)
    return True
