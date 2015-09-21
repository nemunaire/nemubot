# coding=utf-8

"""Get information about subreddit"""

import re

from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools import web

nemubotversion = 3.4

from more import Response


def help_full():
    return "!subreddit /subreddit/: Display information on the subreddit."

LAST_SUBS = dict()


@hook("cmd_hook", "subreddit")
def cmd_subreddit(msg):
    global LAST_SUBS
    if not len(msg.args):
        if msg.channel in LAST_SUBS and len(LAST_SUBS[msg.channel]) > 0:
            subs = [LAST_SUBS[msg.channel].pop()]
        else:
            raise IRCException("Which subreddit? Need inspiration? "
                               "type !horny or !bored")
    else:
        subs = msg.args

    all_res = list()
    for osub in subs:
        sub = re.match(r"^/?(?:(\w)/)?(\w+)/?$", osub)
        if sub is not None:
            if sub.group(1) is not None and sub.group(1) != "":
                where = sub.group(1)
            else:
                where = "r"

            sbr = web.getJSON("http://www.reddit.com/%s/%s/about.json" %
                              (where, sub.group(2)))

            if sbr is None:
                raise IRCException("subreddit not found")

            if "title" in sbr["data"]:
                res = Response(channel=msg.channel,
                               nomore="No more information")
                res.append_message(
                    ("[NSFW] " if sbr["data"]["over18"] else "") +
                    sbr["data"]["url"] + " " + sbr["data"]["title"] + ": " +
                    sbr["data"]["public_description" if sbr["data"]["public_description"] != "" else "description"].replace("\n", " ") +
                    " %s subscriber(s)" % sbr["data"]["subscribers"])
                if sbr["data"]["public_description"] != "":
                    res.append_message(
                        sbr["data"]["description"].replace("\n", " "))
                all_res.append(res)
            else:
                all_res.append(Response("/%s/%s doesn't exist" %
                                        (where, sub.group(2)),
                                        channel=msg.channel))
        else:
            all_res.append(Response("%s is not a valid subreddit" % osub,
                                    channel=msg.channel, nick=msg.nick))

    return all_res


@hook("msg_default")
def parselisten(msg):
    parseresponse(msg)
    return None


@hook("all_post")
def parseresponse(msg):
    global LAST_SUBS

    try:
        urls = re.findall("www.reddit.com(/\w/\w+/?)", msg.text)
        for url in urls:
            for recv in msg.receivers:
                if recv not in LAST_SUBS:
                    LAST_SUBS[recv] = list()
                LAST_SUBS[recv].append(url)
    except:
        pass

    return msg
