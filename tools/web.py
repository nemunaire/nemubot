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
import re
import socket
from urllib.parse import quote

import xmlparser

# Parse URL

def parseURL(url):
    """Separate protocol, domain, port and page request"""
    res = re.match("^(([^:]+)://)?([^:/]+)(:([0-9]{1,5}))?(.*)$", url)
    if res is not None:
        if res.group(5) is not None:
            port = int(res.group(5))
        elif res.group(2) is not None:
            if res.group(2) == "http":
                port = 80
            elif res.group(2) == "https":
                port = 443
            else:
                print ("<tools.web> WARNING: unknown protocol %s"
                       % res.group(2))
                port = 0
        else:
            port = 0
        return (res.group(2), res.group(3), port, res.group(6))
    else:
        return (None, None, None, None)

def getDomain(url):
    """Return the domain of a given URL"""
    (protocol, domain, port, page) = parseURL(url)
    return domain

def getProtocol(url):
    """Return the protocol of a given URL"""
    (protocol, domain, port, page) = parseURL(url)
    return protocol

def getPort(url):
    """Return the port of a given URL"""
    (protocol, domain, port, page) = parseURL(url)
    return port

def getRequest(url):
    """Return the page request of a given URL"""
    (protocol, domain, port, page) = parseURL(url)
    return page


# Get real pages

def getURLContent(url, timeout=15):
    """Return page content corresponding to URL or None if any error occurs"""
    (protocol, domain, port, page) = parseURL(url)
    if port == 0: port = 80
    conn = http.client.HTTPConnection(domain, port=port, timeout=15)
    try:
        conn.request("GET", page, None, {"User-agent": "Nemubot v3"})
    except socket.gaierror:
        print ("<tools.web> Unable to receive page %s from %s on %d."
               % (page, domain, port))
        return None

    res = conn.getresponse()
    data = res.read()

    conn.close()

    if res.status == http.client.OK or res.status == http.client.SEE_OTHER:
        return data
    #TODO: follow redirections
    else:
        return None

def getXML(url, timeout=15):
    """Get content page and return XML parsed content"""
    cnt = getURLContent(url, timeout)
    if cnt is None:
        return None
    else:
        return xmlparser.parse_string(cnt)

# Other utils

def striphtml(data):
    """Remove HTML tags from text"""
    p = re.compile(r'<.*?>')
    return p.sub('', data).replace("&#x28;", "/(").replace("&#x29;", ")/").replace("&#x22;", "\"")


# Tests when called alone
if __name__ == "__main__":
    print(parseURL("www.nemunai.re"))
    print(parseURL("www.nemunai.re/?p0m"))
    print(parseURL("http://www.nemunai.re/?p0m"))
    print(parseURL("http://www.nemunai.re:42/?p0m"))
    print(parseURL("www.nemunai.re:42/?p0m"))
    print(parseURL("http://www.nemunai.re/?p0m"))
