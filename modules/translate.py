# coding=utf-8

import http.client
import re
import socket
import json
from urllib.parse import quote
from urllib.request import urlopen

nemubotversion = 3.4

import xmlparser

LANG = ["ar", "zh", "cz", "en", "fr", "gr", "it",
        "ja", "ko", "pl", "pt", "ro", "es", "tr"]
URL = "http://api.wordreference.com/0.8/%s/json/%%s%%s/%%s"

def load(context):
    global URL
    if not CONF or not CONF.hasNode("wrapi") or not CONF.getNode("wrapi").hasAttribute("key"):
        print ("You need a WordReference API key in order to use this module."
               " Add it to the module configuration file:\n<wrapi key=\"XXXXX\""
               " />\nRegister at "
               "http://www.wordreference.com/docs/APIregistration.aspx")
        return None
    else:
        URL = URL % CONF.getNode("wrapi")["key"]

    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_translate, "translate"))


def help_tiny():
    """Line inserted in the response to the command !help"""
    return "Translation module"

def help_full():
    return "!translate [lang] <term>[ <term>[...]]: Found translation of <term> from/to english to/from <lang>. Data © WordReference.com"


def cmd_translate(msg):
    if len(msg.cmds) < 2:
        raise IRCException("which word would you translate?")

    if len(msg.cmds) > 3 and msg.cmds[1] in LANG and msg.cmds[2] in LANG:
        if msg.cmds[1] != "en" and msg.cmds[2] != "en":
            raise IRCException("sorry, I can only translate to or from english")
        langFrom = msg.cmds[1]
        langTo = msg.cmds[2]
        term = ' '.join(msg.cmds[3:])
    elif len(msg.cmds) > 2 and msg.cmds[1] in LANG:
        langFrom = msg.cmds[1]
        if langFrom == "en":
            langTo = "fr"
        else:
            langTo = "en"
        term = ' '.join(msg.cmds[2:])
    else:
        langFrom = "en"
        langTo = "fr"
        term = ' '.join(msg.cmds[1:])

    try:
        raw = urlopen(URL % (langFrom, langTo, quote(term)))
    except:
        raise IRCException("invalid request")
    wres = json.loads(raw.read().decode())

    if "Error" in wres:
        raise IRCException(wres["Note"])

    else:
        res = Response(msg.sender, channel=msg.channel,
                       count=" (%d more meanings)",
                       nomore="No more translation")
        for k in sorted(wres.keys()):
            t = wres[k]
            if len(k) > 4 and k[:4] == "term":
                if "Entries" in t:
                    ent = t["Entries"]
                else:
                    ent = t["PrincipalTranslations"]

                for i in sorted(ent.keys()):
                    res.append_message("Translation of %s%s: %s" % (
                        ent[i]["OriginalTerm"]["term"],
                        meaning(ent[i]["OriginalTerm"]),
                        extract_traslation(ent[i])))
        return res

def meaning(entry):
    ret = list()
    if "sense" in entry and len(entry["sense"]) > 0:
        ret.append('« %s »' % entry["sense"])
    if "usage" in entry and len(entry["usage"]) > 0:
        ret.append(entry["usage"])
    if len(ret) > 0:
        return " as " + "/".join(ret)
    else:
        return ""

def extract_traslation(entry):
    ret = list()
    for i in [ "FirstTranslation", "SecondTranslation", "ThirdTranslation", "FourthTranslation" ]:
        if i in entry:
            ret.append("\x03\x02%s\x03\x02%s" % (entry[i]["term"], meaning(entry[i])))
    if "Note" in entry and entry["Note"]:
        ret.append("note: %s" % entry["Note"])
    return ", ".join(ret)
