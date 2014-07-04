# coding=utf-8

import datetime
import json
import re
from urllib.parse import quote
from urllib.request import urlopen

nemubotversion = 3.3

API_URL="http://worldcup.sfg.io/%s"

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_watch, "watch_worldcup"))
    add_hook("cmd_hook", Hook(cmd_worldcup, "worldcup"))

    from event import ModuleEvent
    add_event(ModuleEvent(func=lambda url: urlopen(url).read().decode(), func_data=API_URL % "matches/current?by_date=DESC", call=current_match_new_action, intervalle=30))


def help_tiny ():
    """Line inserted in the response to the command !help"""
    return "The 2014 football worldcup module"

def help_full ():
    return "!worldcup: do something."


def start_watch(msg):
    global DATAS
    w = ModuleState("watch")
    w["server"] = msg.server
    w["channel"] = msg.channel
    w["proprio"] = msg.nick
    w["sender"] = msg.sender
    w["start"] = datetime.datetime.now()
    DATAS.addChild(w)
    save()
    raise IRCException("This channel is now watching world cup events!")

def cmd_watch(msg):
    global DATAS

    # Get current state
    node = None
    for n in DATAS.getChilds():
        if n["server"] == msg.server and n["channel"] == msg.channel:
            node = n
            break

    if len(msg.cmds) >= 2:
        if msg.cmds[1] == "stop" and node is not None:
            DATAS.delChild(node)
            save()
            raise IRCException("This channel will not anymore receives world cup events.")
        elif msg.cmds[1] == "start" and node is None:
            start_watch(msg)
        else:
            raise IRCException("Use only start or stop as first argument")
    else:
        if node is None:
            start_watch(msg)
        else:
            DATAS.delChild(node)
            save()
            raise IRCException("This channel will not anymore receives world cup events.")

def current_match_new_action(match_str, osef):
    global DATAS

    add_event(ModuleEvent(func=lambda url: urlopen(url).read().decode(), func_data=API_URL % "matches/current?by_date=DESC", call=current_match_new_action, intervalle=30))

    matches = json.loads(match_str)

    for match in matches:
        if is_valid(match):
            events = sort_events(match["home_team"], match["away_team"], match["home_team_events"], match["away_team_events"])
            msg = "Match %s vs. %s ; score %s - %s" % (match["home_team"]["country"], match["away_team"]["country"], match["home_team"]["goals"], match["away_team"]["goals"])

            if len(events) > 0:
                msg += " ; à la " + txt_event(events[0])

            for n in DATAS.getChilds():
                send_response(n["server"], Response(n["sender"], msg, channel=n["channel"]))

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def sort_events(teamA, teamB, eventA, eventB):
    res = []

    for e in eventA:
        e["team"] = teamA
        res.append(e)
    for e in eventB:
        e["team"] = teamB
        res.append(e)

    return sorted(res, key=lambda evt: int(evt["time"][0:2]), reverse=True)

def detail_event(evt):
    if evt == "yellow-card":
        return "carton jaune pour"
    elif evt == "yellow-card-second":
        return "second carton jaune pour"
    elif evt == "red-card":
        return "carton rouge pour"
    elif evt == "substitution-in" or evt == "substitution-in halftime":
        return "joueur entrant :"
    elif evt == "substitution-out" or evt == "substitution-out halftime":
        return "joueur sortant :"
    elif evt == "goal":
        return "but de"
    elif evt == "goal-own":
        return "but contre son camp de"
    elif evt == "goal-penalty":
        return "but (pénalty) de"
    return evt + " par"

def txt_event(e):
    return "%se minutes : %s %s (%s)" % (e["time"], detail_event(e["type_of_event"]), e["player"], e["team"]["code"])

def prettify(match):
    matchdate_local = datetime.datetime.strptime(match["datetime"].replace(':', ''), "%Y-%m-%dT%H%M%S.%f%z")
    matchdate = matchdate_local - (matchdate_local.utcoffset() - datetime.timedelta(hours=2))
    if match["status"] == "future":
        return ["Match à venir (%s) le %s : %s vs. %s" % (match["match_number"], matchdate.strftime("%A %d à %H:%M"), match["home_team"]["country"], match["away_team"]["country"])]
    else:
        msgs = list()
        msg = ""
        if match["status"] == "completed":
            msg += "Match (%s) du %s terminé : " % (match["match_number"], matchdate.strftime("%A %d à %H:%M"))
        else:
            msg += "Match en cours (%s) depuis %d minutes : " % (match["match_number"], (datetime.datetime.now(matchdate.tzinfo) - matchdate_local).seconds / 60)

        msg += "%s %d - %d %s" % (match["home_team"]["country"], match["home_team"]["goals"], match["away_team"]["goals"], match["away_team"]["country"])

        events = sort_events(match["home_team"], match["away_team"], match["home_team_events"], match["away_team_events"])

        if len(events) > 0:
            msg += " ; dernière action, à la " + txt_event(events[0])
            msgs.append(msg)

            for e in events[1:]:
                msgs.append("À la " + txt_event(e))
        else:
            msgs.append(msg)

        return msgs


def is_valid(match):
    return isinstance(match, dict) and (
        isinstance(match.get('home_team'), dict) and
        'goals' in match.get('home_team')
    ) and (
        isinstance(match.get('away_team'), dict) and
        'goals' in match.get('away_team')
    ) or isinstance(match.get('group_id'), int)

def get_match(url, matchid):
    allm = get_matches(url)
    for m in allm:
        if int(m["match_number"]) == matchid:
            return [ m ]

def get_matches(url):
    try:
        raw = urlopen(url)
    except:
        raise IRCException("requête invalide")
    matches = json.loads(raw.read().decode())

    for match in matches:
        if is_valid(match):
            yield match

def cmd_worldcup(msg):
    res = Response(msg.sender, channel=msg.channel, nomore="No more match to display", count=" (%d more matches)")
    nb = len(msg.cmds)

    url = None
    if nb == 2:
        if msg.cmds[1] == "today" or msg.cmds[1] == "aujourd'hui":
            url = "matches/today?by_date=ASC"
        elif msg.cmds[1] == "tomorrow" or msg.cmds[1] == "demain":
            url = "matches/tomorrow?by_date=ASC"
        elif msg.cmds[1] == "all" or msg.cmds[1] == "tout" or msg.cmds[1] == "tous":
            url = "matches/"
        elif len(msg.cmds[1]) == 3:
            url = "matches/country?fifa_code=%s&by_date=DESC" % msg.cmds[1]
        elif is_int(msg.cmds[1]):
            url = int(msg.cmds[1])
        else:
            raise IRCException("unrecognized request; choose between 'today', 'tomorrow', a FIFA country code or a match identifier")

    if url is None:
        url = "matches/current?by_date=ASC"
        res.nomore = "There is no match currently"

    if isinstance(url, int):
        matches = get_match(API_URL % "matches/", url)
    else:
        matches = [m for m in get_matches(API_URL % url)]

    for match in matches:
        if len(matches) == 1:
            res.count = " (%d more actions)"
            for m in prettify(match):
                res.append_message(m)
        else:
            res.append_message(prettify(match)[0])

    return res
