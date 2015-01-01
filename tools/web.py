# coding=utf-8

# Nemubot is a modulable IRC bot, built around XML configuration files.
# Copyright (C) 2012  Mercier Pierre-Olivier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from html.entities import name2codepoint
import http.client
import json
import re
import socket
from urllib.parse import quote
from urllib.parse import urlparse
from urllib.request import urlopen

from exception import IRCException
from tools.xmlparser import parse_string


def isURL(url):
    """Return True if the URL can be parsed"""
    o = urlparse(url)
    return o.scheme == "" and o.netloc == "" and o.path == ""


def getScheme(url):
    """Return the protocol of a given URL"""
    o = urlparse(url)
    return o.scheme


def getHost(url):
    """Return the domain of a given URL"""
    return urlparse(url).hostname


def getPort(url):
    """Return the port of a given URL"""
    return urlparse(url).port


def getPath(url):
    """Return the page request of a given URL"""
    return urlparse(url).path


def getUser(url):
    """Return the page request of a given URL"""
    return urlparse(url).username


def getPassword(url):
    """Return the page request of a given URL"""
    return urlparse(url).password


# Get real pages

def getURLContent(url, timeout=15):
    """Return page content corresponding to URL or None if any error occurs"""
    o = urlparse(url)
    if o.netloc == "":
        o = urlparse("http://" + url)

    if o.scheme == "http":
        conn = http.client.HTTPConnection(o.hostname, port=o.port,
                                          timeout=timeout)
    elif o.scheme == "https":
        conn = http.client.HTTPSConnection(o.hostname, port=o.port,
                                           timeout=timeout)
    elif o.scheme is None or o.scheme == "":
        conn = http.client.HTTPConnection(o.hostname, port=80, timeout=timeout)
    else:
        return None
    try:
        if o.query != '':
            conn.request("GET", o.path + "?" + o.query,
                         None, {"User-agent": "Nemubot v3"})
        else:
            conn.request("GET", o.path, None, {"User-agent": "Nemubot v3"})
    except socket.timeout:
        return None
    except OSError: # [Errno 113] No route to host
        return None
    except socket.gaierror:
        print ("<tools.web> Unable to receive page %s on %s from %s."
               % (o.path, o.netloc, url))
        return None

    try:
        res = conn.getresponse()
        size = int(res.getheader("Content-Length", 524288))
        cntype = res.getheader("Content-Type")

        if size > 524288 or (cntype is not None and cntype[:4] != "text" and cntype[:4] != "appl"):
            return None

        data = res.read(size)

        # Decode content
        charset = "utf-8"
        if cntype is not None:
            lcharset = res.getheader("Content-Type").split(";")
            if len(lcharset) > 1:
                for c in charset:
                    ch = c.split("=")
                    if ch[0].strip().lower() == "charset" and len(ch) > 1:
                        cha = ch[1].split(".")
                        if len(cha) > 1:
                            charset = cha[1]
                        else:
                            charset = cha[0]
    except http.client.BadStatusLine:
        raise IRCException("Invalid HTTP response")
    finally:
        conn.close()

    if res.status == http.client.OK or res.status == http.client.SEE_OTHER:
        return data.decode(charset)
    elif ((res.status == http.client.FOUND or
           res.status == http.client.MOVED_PERMANENTLY) and
          res.getheader("Location") != url):
        return getURLContent(res.getheader("Location"), timeout)
    else:
        raise IRCException("A HTTP error occurs: %d - %s" %
                           (res.status, http.client.responses[res.status]))


def getXML(url, timeout=15):
    """Get content page and return XML parsed content"""
    cnt = getURLContent(url, timeout)
    if cnt is None:
        return None
    else:
        return parse_string(cnt.encode())


def getJSON(url, timeout=15):
    """Get content page and return JSON content"""
    cnt = getURLContent(url, timeout)
    if cnt is None:
        return None
    else:
        return json.loads(cnt)


# Other utils

def htmlentitydecode(s):
    """Decode htmlentities"""
    return re.sub('&(%s);' % '|'.join(name2codepoint),
                  lambda m: chr(name2codepoint[m.group(1)]), s)


def striphtml(data):
    """Remove HTML tags from text"""
    p = re.compile(r'<.*?>')
    return htmlentitydecode(p.sub('', data)
                            .replace("&#x28;", "/(")
                            .replace("&#x29;", ")/")
                            .replace("&#x22;", "\""))
