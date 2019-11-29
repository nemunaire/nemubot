"""The NNTP module"""

# PYTHON STUFFS #######################################################

import email
import email.policy
from email.utils import mktime_tz, parseaddr, parsedate_tz
from functools import partial
from nntplib import NNTP, decode_header
import re
import time
from datetime import datetime
from zlib import adler32

from nemubot import context
from nemubot.event import ModuleEvent
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools.xmlparser.node import ModuleState

from nemubot.module.more import Response


# LOADING #############################################################

def load(context):
    for wn in context.data.getNodes("watched_newsgroup"):
        watch(**wn.attributes)


# MODULE CORE #########################################################

def list_groups(group_pattern="*", **server):
    with NNTP(**server) as srv:
        response, l = srv.list(group_pattern)
        for i in l:
            yield i.group, srv.description(i.group), i.flag

def read_group(group, **server):
    with NNTP(**server) as srv:
        response, count, first, last, name = srv.group(group)
        resp, overviews = srv.over((first, last))
        for art_num, over in reversed(overviews):
            yield over

def read_article(msg_id, **server):
    with NNTP(**server) as srv:
        response, info = srv.article(msg_id)
        return email.message_from_bytes(b"\r\n".join(info.lines), policy=email.policy.SMTPUTF8)


servers_lastcheck = dict()
servers_lastseen = dict()

def whatsnew(group="*", **server):
    fill = dict()
    if "user" in server: fill["user"] = server["user"]
    if "password" in server: fill["password"] = server["password"]
    if "host" in server: fill["host"] = server["host"]
    if "port" in server: fill["port"] = server["port"]

    idx = _indexServer(**server)
    if idx in servers_lastcheck and servers_lastcheck[idx] is not None:
        date_last_check = servers_lastcheck[idx]
    else:
        date_last_check = datetime.now()

    if idx not in servers_lastseen:
        servers_lastseen[idx] = []

    with NNTP(**fill) as srv:
        response, servers_lastcheck[idx] = srv.date()

        response, groups = srv.newgroups(date_last_check)
        for g in groups:
            yield g

        response, articles = srv.newnews(group, date_last_check)
        for msg_id in articles:
            if msg_id not in servers_lastseen[idx]:
                servers_lastseen[idx].append(msg_id)
                response, info = srv.article(msg_id)
                yield email.message_from_bytes(b"\r\n".join(info.lines))

        # Clean huge lists
        if len(servers_lastseen[idx]) > 42:
            servers_lastseen[idx] = servers_lastseen[idx][23:]


def format_article(art, **response_args):
    art["X-FromName"], art["X-FromEmail"] = parseaddr(art["From"] if "From" in art else "")
    if art["X-FromName"] == '': art["X-FromName"] = art["X-FromEmail"]

    date = mktime_tz(parsedate_tz(art["Date"]))
    if date < time.time() - 120:
        title = "\x0314In \x0F\x03{0:02d}{Newsgroups}\x0F\x0314: on \x0F{Date}\x0314 by \x0F\x03{0:02d}{X-FromName}\x0F \x02{Subject}\x0F"
    else:
        title = "\x0314In \x0F\x03{0:02d}{Newsgroups}\x0F\x0314: by \x0F\x03{0:02d}{X-FromName}\x0F \x02{Subject}\x0F"

    return Response(art.get_payload().replace('\n', ' '),
                    title=title.format(adler32(art["Newsgroups"].encode()) & 0xf, adler32(art["X-FromEmail"].encode()) & 0xf, **{h: decode_header(i) for h,i in art.items()}),
                    **response_args)


watches = dict()

def _indexServer(**kwargs):
    if "user" not in kwargs: kwargs["user"] = ""
    if "password" not in kwargs: kwargs["password"] = ""
    if "host" not in kwargs: kwargs["host"] = ""
    if "port" not in kwargs: kwargs["port"] = 119
    return "{user}:{password}@{host}:{port}".format(**kwargs)

def _newevt(**args):
    context.add_event(ModuleEvent(call=partial(_ticker, **args), interval=42))

def _ticker(to_server, to_channel, group, server):
    _newevt(to_server=to_server, to_channel=to_channel, group=group, server=server)
    n = 0
    for art in whatsnew(group, **server):
        n += 1
        if n > 10:
            continue
        context.send_response(to_server, format_article(art, channel=to_channel))
    if n > 10:
        context.send_response(to_server, Response("... and %s others news" % (n - 10), channel=to_channel))

def watch(to_server, to_channel, group="*", **server):
    _newevt(to_server=to_server, to_channel=to_channel, group=group, server=server)


# MODULE INTERFACE ####################################################

keywords_server = {
    "host=HOST": "hostname or IP of the NNTP server",
    "port=PORT": "port of the NNTP server",
    "user=USERNAME": "username to use to connect to the server",
    "password=PASSWORD": "password to use to connect to the server",
}

@hook.command("nntp_groups",
      help="Show list of existing groups",
      help_usage={
          None: "Display all groups",
          "PATTERN": "Filter on group matching the PATTERN"
      },
      keywords=keywords_server)
def cmd_groups(msg):
    if "host" not in msg.kwargs:
        raise IMException("please give a hostname in keywords")

    return Response(["\x02\x03{0:02d}{1}\x0F: {2}".format(adler32(g[0].encode()) & 0xf, *g) for g in list_groups(msg.args[0] if len(msg.args) > 0 else "*", **msg.kwargs)],
                    channel=msg.channel,
                    title="Matching groups on %s" % msg.kwargs["host"])


@hook.command("nntp_overview",
              help="Show an overview of articles in given group(s)",
              help_usage={
                  "GROUP": "Filter on group matching the PATTERN"
              },
              keywords=keywords_server)
def cmd_overview(msg):
    if "host" not in msg.kwargs:
        raise IMException("please give a hostname in keywords")

    if not len(msg.args):
        raise IMException("which group would you overview?")

    for g in msg.args:
        arts = []
        for grp in read_group(g, **msg.kwargs):
            grp["X-FromName"], grp["X-FromEmail"] = parseaddr(grp["from"] if "from" in grp else "")
            if grp["X-FromName"] == '': grp["X-FromName"] = grp["X-FromEmail"]

            arts.append("On {date}, from \x03{0:02d}{X-FromName}\x0F \x02{subject}\x0F: \x0314{message-id}\x0F".format(adler32(grp["X-FromEmail"].encode()) & 0xf, **{h: decode_header(i) for h,i in grp.items()}))

        if len(arts):
            yield Response(arts,
                           channel=msg.channel,
                           title="In \x03{0:02d}{1}\x0F".format(adler32(g[0].encode()) & 0xf, g))


@hook.command("nntp_read",
              help="Read an article from a server",
              help_usage={
                  "MSG_ID": "Read the given message"
              },
              keywords=keywords_server)
def cmd_read(msg):
    if "host" not in msg.kwargs:
        raise IMException("please give a hostname in keywords")

    for msgid in msg.args:
        if not re.match("<.*>", msgid):
            msgid = "<" + msgid + ">"
        art = read_article(msgid, **msg.kwargs)
        yield format_article(art, channel=msg.channel)


@hook.command("nntp_watch",
              help="Launch an event looking for new groups and articles on a server",
              help_usage={
                  None: "Watch all groups",
                  "PATTERN": "Limit the watch on group matching this PATTERN"
              },
              keywords=keywords_server)
def cmd_watch(msg):
    if "host" not in msg.kwargs:
        raise IMException("please give a hostname in keywords")

    if not msg.frm_owner:
        raise IMException("sorry, this command is currently limited to the owner")

    wnnode = ModuleState("watched_newsgroup")
    wnnode["id"] = _indexServer(**msg.kwargs)
    wnnode["to_server"] = msg.server
    wnnode["to_channel"] = msg.channel
    wnnode["group"] = msg.args[0] if len(msg.args) > 0 else "*"

    wnnode["user"] = msg.kwargs["user"] if "user" in msg.kwargs else ""
    wnnode["password"] = msg.kwargs["password"] if "password" in msg.kwargs else ""
    wnnode["host"] = msg.kwargs["host"] if "host" in msg.kwargs else ""
    wnnode["port"] = msg.kwargs["port"] if "port" in msg.kwargs else 119

    context.data.addChild(wnnode)
    watch(**wnnode.attributes)

    return Response("Ok ok, I watch this newsgroup!", channel=msg.channel)
