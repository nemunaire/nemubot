"""Alert on changes on websites"""

import logging
from random import randint
import urllib.parse
from urllib.parse import urlparse

from nemubot.event import ModuleEvent
from nemubot.exception import IRCException
from nemubot.hooks import hook
from nemubot.tools.xmlparser.node import ModuleState

logger = logging.getLogger("nemubot.module.networking.watchWebsite")
nemubotversion = 3.4

from more import Response

from .atom import Atom
from . import page

DATAS = None


def load(datas):
    """Register events on watched website"""

    global DATAS
    DATAS = datas

    DATAS.setIndex("url", "watch")
    for site in DATAS.getNodes("watch"):
        if site.hasNode("alert"):
            start_watching(site, randint(-30, 30))
        else:
            print("No alert defined for this site: " + site["url"])
            #DATAS.delChild(site)


def del_site(url, nick, channel, frm_owner):
    """Remove a site from watching list

    Argument:
    url -- URL to unwatch
    """

    o = urlparse(url, "http")
    if o.scheme != "" and url in DATAS.index:
        site = DATAS.index[url]
        for a in site.getNodes("alert"):
            if a["channel"] == channel:
#                if not (nick == a["nick"] or frm_owner):
#                    raise IRCException("you cannot unwatch this URL.")
                site.delChild(a)
                if not site.hasNode("alert"):
                    del_event(site["_evt_id"])
                    DATAS.delChild(site)
                save()
                return Response("I don't watch this URL anymore.",
                                channel=channel, nick=nick)
    raise IRCException("I didn't watch this URL!")


def add_site(url, nick, channel, server, diffType="diff"):
    """Add a site to watching list

    Argument:
    url -- URL to watch
    """

    o = urlparse(url, "http")
    if o.netloc == "":
        raise IRCException("sorry, I can't watch this URL :(")

    alert = ModuleState("alert")
    alert["nick"] = nick
    alert["server"] = server
    alert["channel"] = channel
    alert["message"] = "{url} just changed!"

    if url not in DATAS.index:
        watch = ModuleState("watch")
        watch["type"] = diffType
        watch["url"] = url
        watch["time"] = 123
        DATAS.addChild(watch)
        watch.addChild(alert)
        start_watching(watch)
    else:
        DATAS.index[url].addChild(alert)

    save()
    return Response(channel=channel, nick=nick,
                    message="this site is now under my supervision.")


def format_response(site, link='%s', title='%s', categ='%s', content='%s'):
    """Format and send response for given site

    Argument:
    site -- DATAS structure representing a site to watch

    Keyword arguments:
    link -- link to the content
    title -- for ATOM feed: title of the new article
    categ -- for ATOM feed: category of the new article
    content -- content of the page/new article
    """

    for a in site.getNodes("alert"):
        send_response(a["server"],
                      Response(a["message"].format(url=site["url"],
                                                   link=link,
                                                   title=title,
                                                   categ=categ,
                                                   content=content),
                               channel=a["channel"],
                               server=a["server"]))


def alert_change(content, site):
    """Function called when a change is detected on a given site

    Arguments:
    content -- The new content
    site -- DATAS structure representing a site to watch
    """

    if site["type"] == "updown":
        if site["lastcontent"] is None:
            site["lastcontent"] = content is not None

        if (content is not None) != site.getBool("lastcontent"):
            format_response(site, link=site["url"])
            site["lastcontent"] = content is not None
        start_watching(site)
        return

    if content is None:
        start_watching(site)
        return

    if site["type"] == "atom":
        if site["_lastpage"] is None:
            if site["lastcontent"] is None or site["lastcontent"] == "":
                site["lastcontent"] = content
            site["_lastpage"] = Atom(site["lastcontent"])
        try:
            page = Atom(content)
        except:
            print("An error occurs during Atom parsing. Restart event...")
            start_watching(site)
            return
        diff = site["_lastpage"].diff(page)
        if len(diff) > 0:
            site["_lastpage"] = page
            diff.reverse()
            for d in diff:
                site.setIndex("term", "category")
                categories = site.index

                if len(categories) > 0:
                    if d.category is None or d.category not in categories:
                        format_response(site, link=d.link, categ=categories[""]["part"], title=d.title)
                    else:
                        format_response(site, link=d.link, categ=categories[d.category]["part"], title=d.title)
                else:
                    format_response(site, link=d.link, title=urllib.parse.unquote(d.title))
        else:
            start_watching(site)
            return  # Stop here, no changes, so don't save

    else:  # Just looking for any changes
        format_response(site, link=site["url"], content=content)
    site["lastcontent"] = content
    start_watching(site)
    save()


def fwatch(url):
    cnt = page.fetch(url, None)
    if cnt is not None:
        render = page._render(cnt)
        if render is None or render == "":
            return cnt
        return render
    return None


def start_watching(site, offset=0):
    """Launch the event watching given site

    Argument:
    site -- DATAS structure representing a site to watch

    Keyword argument:
    offset -- offset time to delay the launch of the first check
    """

    o = urlparse(site["url"], "http")
    #print_debug("Add %s event for site: %s" % (site["type"], o.netloc))

    try:
        evt = ModuleEvent(func=fwatch,
                          cmp_data=site["lastcontent"],
                          func_data=site["url"], offset=offset,
                          interval=site.getInt("time"),
                          call=alert_change, call_data=site)
        site["_evt_id"] = add_event(evt)
    except IRCException:
        logger.exception("Unable to watch %s", site["url"])
