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
from urllib.parse import quote

def parseURL(url):
    """Separate protocol, domain, port and page request"""
    res = re.match("^(([^:]+)://)?([^:/]+)(:([0-9]{1,5}))?(.*)$", url)
    if res is not None:
        port = res.group(5)
        if port is None and res.group(2) is not None:
            if res.group(2) == "http":
                port = 80
            elif res.group(2) == "https":
                port = 443
        return (res.group(2), res.group(3), port, res.group(6))
    else:
        return (None, None, None, None)

def getDomain(url):
    """Return the domain of a given URL"""
    (protocol, domain, port, page) = parseURL(url)
    return domain

def getProtocol(url):
    """Return the domain of a given URL"""
    (protocol, domain, port, page) = parseURL(url)
    return protocol

def getURL(url):
    """Return page content corresponding to URL or None if any error occurs"""
    conn = http.client.HTTPConnection("api.duckduckgo.com", timeout=5)
    try:
        conn.request("GET", "/?q=%s&format=xml" % quote(terms))
    except socket.gaierror:
        print ("impossible de récupérer la page %s."%(p))
        return (http.client.INTERNAL_SERVER_ERROR, None)

    res = conn.getresponse()
    data = res.read()

    conn.close()
    return (res.status, data)

if __name__ == "__main__":
  content1 = ""
  with open("rss.php.1", "r") as f:
    for line in f:
      content1 += line
  content2 = ""
  with open("rss.php", "r") as f:
    for line in f:
      content2 += line
  a = Atom (content1)
  print (a.updated)
  b = Atom (content2)
  print (b.updated)

  diff = a.diff (b)
  print (diff)
