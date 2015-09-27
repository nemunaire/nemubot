#!/usr/bin/python3
# coding=utf-8

import datetime
import time
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation


class AtomEntry:

    def __init__(self, node):
        self.id = node.getElementsByTagName("id")[0].firstChild.nodeValue
        if node.getElementsByTagName("title")[0].firstChild is not None:
            self.title = node.getElementsByTagName("title")[0].firstChild.nodeValue
        else:
            self.title = ""
        try:
            self.updated = time.strptime(node.getElementsByTagName("updated")[0].firstChild.nodeValue[:19], "%Y-%m-%dT%H:%M:%S")
        except:
            try:
                self.updated = time.strptime(node.getElementsByTagName("updated")[0].firstChild.nodeValue[:10], "%Y-%m-%d")
            except:
                print(node.getElementsByTagName("updated")[0].firstChild.nodeValue[:10])
                self.updated = time.localtime()
        self.updated = datetime.datetime(*self.updated[:6])
        if len(node.getElementsByTagName("summary")) > 0 and node.getElementsByTagName("summary")[0].firstChild is not None:
            self.summary = node.getElementsByTagName("summary")[0].firstChild.nodeValue
        else:
            self.summary = None
        if len(node.getElementsByTagName("link")) > 0:
            self.link = node.getElementsByTagName("link")[0].getAttribute("href")
        else:
            self.link = None
        if len(node.getElementsByTagName("category")) >= 1:
            self.category = node.getElementsByTagName("category")[0].getAttribute("term")
        else:
            self.category = None
        if len(node.getElementsByTagName("link")) > 1:
            self.link2 = node.getElementsByTagName("link")[1].getAttribute("href")
        else:
            self.link2 = None

    def __repr__(self):
        return "<AtomEntry title='%s' updated='%s'>" % (self.title, self.updated)

    def __cmp__(self, other):
        return not (self.id == other.id)


class RSSEntry:

    def __init__(self, node):
        self.id = node.getElementsByTagName("guid")[0].firstChild.nodeValue
        if node.getElementsByTagName("title")[0].firstChild is not None:
            self.title = node.getElementsByTagName("title")[0].firstChild.nodeValue
        else:
            self.title = ""

        self.pubDate = node.getElementsByTagName("pubDate")[0].firstChild.nodeValue

        if len(node.getElementsByTagName("description")) > 0 and node.getElementsByTagName("description")[0].firstChild is not None:
            self.summary = node.getElementsByTagName("description")[0].firstChild.nodeValue
        else:
            self.summary = None
        if len(node.getElementsByTagName("link")) > 0:
            self.link = node.getElementsByTagName("link")[0].getAttribute("href")
        else:
            self.link = None

    def __repr__(self):
        return "<RSSEntry title='%s' updated='%s'>" % (self.title, self.pubDate)

    def __cmp__(self, other):
        return not (self.id == other.id)


class Feed:

    def __init__(self, string):
        self.feed = parseString(string).documentElement
        self.id = None
        self.title = None
        self.updated = None
        self.entries = list()

        if self.feed.tagName == "rss":
            self._parse_rss_feed()
        elif self.feed.tagName == "feed":
            self._parse_atom_feed()
        else:
            from nemubot.exception import IRCException
            raise IRCException("This is not a valid Atom or RSS feed")


    def _parse_atom_feed(self):
        self.id = self.feed.getElementsByTagName("id")[0].firstChild.nodeValue
        self.title = self.feed.getElementsByTagName("title")[0].firstChild.nodeValue

        for item in self.feed.getElementsByTagName("entry"):
            self._add_entry(AtomEntry(item))


    def _parse_rss_feed(self):
        self.title = self.feed.getElementsByTagName("title")[0].firstChild.nodeValue

        for item in self.feed.getElementsByTagName("item"):
            self._add_entry(RSSEntry(item))


    def _add_entry(self, entry):
        if entry is not None:
            self.entries.append(entry)
            if hasattr(entry, "updated") and (self.updated is None or self.updated < entry.updated):
                self.updated = entry.updated


    def __and__(self, b):
        ret = []

        for e in self.entries:
            if e not in b.entries:
                ret.append(e)

        for e in b.entries:
            if e not in self.entries:
                ret.append(e)

        # TODO: Sort by date

        return ret
