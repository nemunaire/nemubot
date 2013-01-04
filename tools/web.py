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

import http.client
import json
import re
import socket
from urllib.parse import quote

import xmlparser

# Parse URL

def parseURL(url):
    """Separate protocol, domain, port and page request"""
    res = re.match("^([a-zA-Z0-9+.-]+):(//)?(.*)$", url)
    if res is not None:
        scheme = res.group(1)
        if scheme == "https":
            port = 443
        elif scheme == "http":
            port = 80
        elif scheme == "ftp":
            port = 21
        elif scheme == "telnet":
            port = 23
        else:
            port = 0
        if res.group(2) == "//":
            # Waiting Common Internet Scheme Syntax
            ciss = re.match("^(([^:]+)(:([^@]+))@)?([^:/]+)(:([0-9]+))?(/.*)$", res.group(3))
            user = ciss.group(2)
            password = ciss.group(4)
            host = ciss.group(5)
            if ciss.group(7) is not None and ciss.group(7) != "" and int(ciss.group(7)) > 0:
                port = int(ciss.group(7))
            path = ciss.group(8)
            return (scheme, (user, password), host, port, path)
        else:
            return (scheme, (None, None), None, None, res.group(3))
    else:
        return (None, (None, None), None, None, None)

def isURL(url):
    """Return True if the URL can be parsed"""
    (scheme, (user, password), host, port, path) = parseURL(url)
    return scheme is not None

def getScheme(url):
    """Return the protocol of a given URL"""
    (scheme, (user, password), host, port, path) = parseURL(url)
    return scheme

def getHost(url):
    """Return the domain of a given URL"""
    (scheme, (user, password), host, port, path) = parseURL(url)
    return host

def getPort(url):
    """Return the port of a given URL"""
    (scheme, (user, password), host, port, path) = parseURL(url)
    return port

def getPath(url):
    """Return the page request of a given URL"""
    (scheme, (user, password), host, port, path) = parseURL(url)
    return path

def getUser(url):
    """Return the page request of a given URL"""
    (scheme, (user, password), host, port, path) = parseURL(url)
    return user
def getPassword(url):
    """Return the page request of a given URL"""
    (scheme, (user, password), host, port, path) = parseURL(url)
    return password


# Get real pages

def getURLContent(url, timeout=15):
    """Return page content corresponding to URL or None if any error occurs"""
    (scheme, (user, password), host, port, path) = parseURL(url)
    if port is None:
        return None
    conn = http.client.HTTPConnection(host, port=port, timeout=timeout)
    try:
        conn.request("GET", path, None, {"User-agent": "Nemubot v3"})
    except socket.timeout:
        return None
    except socket.gaierror:
        print ("<tools.web> Unable to receive page %s from %s on %d."
               % (path, host, port))
        return None

    try:
        res = conn.getresponse()
        size = int(res.getheader("Content-Length", 5000))
        cntype = res.getheader("Content-Type")

        if size > 10000 or cntype[:4] != "text":
            return None

        data = res.read(size)
    except http.client.BadStatusLine:
        return None
    finally:
        conn.close()

    if res.status == http.client.OK or res.status == http.client.SEE_OTHER:
        return data
    elif res.status == http.client.FOUND or res.status == http.client.MOVED_PERMANENTLY:
        return getURLContent(res.getheader("Location"), timeout)
    else:
        return None

def getXML(url, timeout=15):
    """Get content page and return XML parsed content"""
    cnt = getURLContent(url, timeout)
    if cnt is None:
        return None
    else:
        return xmlparser.parse_string(cnt)

def getJSON(url, timeout=15):
    """Get content page and return JSON content"""
    cnt = getURLContent(url, timeout)
    if cnt is None:
        return None
    else:
        return json.loads(cnt.decode())

def traceURL(url, timeout=5, stack=None):
    """Follow redirections and return the redirections stack"""
    if stack is None:
        stack = list()
    stack.append(url)

    (scheme, (user, password), host, port, path) = parseURL(url)
    if port is None or port == 0:
        return stack
    conn = http.client.HTTPConnection(host, port=port, timeout=timeout)
    try:
        conn.request("HEAD", path, None, {"User-agent": "Nemubot v3"})
    except socket.timeout:
        stack.append("Timeout")
        return stack
    except socket.gaierror:
        print ("<tools.web> Unable to receive page %s from %s on %d."
               % (path, host, port))
        return None

    try:
        res = conn.getresponse()
    except http.client.BadStatusLine:
        return None
    finally:
        conn.close()

    if res.status == http.client.OK:
        return stack
    elif res.status == http.client.FOUND or res.status == http.client.MOVED_PERMANENTLY or res.status == http.client.SEE_OTHER:
        url = res.getheader("Location")
        if url in stack:
            stack.append(url)
            return stack
        else:
            return traceURL(url, timeout, stack)
    else:
        return None


# Other utils

def striphtml(data):
    """Remove HTML tags from text"""
    p = re.compile(r'<.*?>')
    return p.sub('', data).replace("&#x28;", "/(").replace("&#x29;", ")/").replace("&#x22;", "\"")


# Tests when called alone
if __name__ == "__main__":
    print(parseURL("http://www.nemunai.re/"))
    print(parseURL("http://www.nemunai.re/?p0m"))
    print(parseURL("http://www.nemunai.re/?p0m"))
    print(parseURL("http://www.nemunai.re:42/?p0m"))
    print(parseURL("ftp://www.nemunai.re:42/?p0m"))
    print(parseURL("http://www.nemunai.re/?p0m"))
    print(parseURL("magnet:ceciestunmagnet!"))
