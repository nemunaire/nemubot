# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2015  Mercier Pierre-Olivier
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

from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit
import socket

from nemubot.exception import IMException


def isURL(url):
    """Return True if the URL can be parsed"""
    o = urlparse(_getNormalizedURL(url))
    return o.netloc == "" and o.path == ""


def _getNormalizedURL(url):
    """Return a light normalized form for the given URL"""
    return url if "//" in url or ":" in url else "//" + url

def getNormalizedURL(url):
    """Return a normalized form for the given URL"""
    return urlunsplit(urlsplit(_getNormalizedURL(url), "http"))


def getScheme(url):
    """Return the protocol of a given URL"""
    o = urlparse(url, "http")
    return o.scheme


def getHost(url):
    """Return the domain of a given URL"""
    return urlparse(_getNormalizedURL(url), "http").hostname


def getPort(url):
    """Return the port of a given URL"""
    return urlparse(_getNormalizedURL(url), "http").port


def getPath(url):
    """Return the page request of a given URL"""
    return urlparse(_getNormalizedURL(url), "http").path


def getUser(url):
    """Return the page request of a given URL"""
    return urlparse(_getNormalizedURL(url), "http").username


def getPassword(url):
    """Return the page request of a given URL"""
    return urlparse(_getNormalizedURL(url), "http").password


# Get real pages

def getURLContent(url, body=None, timeout=7, header=None, decode_error=False,
                  max_size=524288):
    """Return page content corresponding to URL or None if any error occurs

    Arguments:
    url -- the URL to get
    body -- Data to send as POST content
    timeout -- maximum number of seconds to wait before returning an exception
    decode_error -- raise exception on non-200 pages or ignore it
    max_size -- maximal size allow for the content
    """

    o = urlparse(_getNormalizedURL(url), "http")

    import http.client

    kwargs = {
        'host': o.hostname,
        'port': o.port,
        'timeout': timeout
    }

    if o.scheme == "http":
        conn = http.client.HTTPConnection(**kwargs)
    elif o.scheme == "https":
        # For Python>3.4, restore the Python 3.3 behavior
        import ssl
        if hasattr(ssl, "create_default_context"):
            kwargs["context"] = ssl.create_default_context()
            kwargs["context"].check_hostname = False
            kwargs["context"].verify_mode = ssl.CERT_NONE

        conn = http.client.HTTPSConnection(**kwargs)
    elif o.scheme is None or o.scheme == "":
        conn = http.client.HTTPConnection(**kwargs)
    else:
        raise IMException("Invalid URL")

    from nemubot import __version__
    if header is None:
        header = {"User-agent": "Nemubot v%s" % __version__}
    elif "User-agent" not in header:
        header["User-agent"] = "Nemubot v%s" % __version__

    if body is not None and "Content-Type" not in header:
        header["Content-Type"] = "application/x-www-form-urlencoded"

    import socket
    try:
        if o.query != '':
            conn.request("GET" if body is None else "POST",
                         o.path + "?" + o.query,
                         body,
                         header)
        else:
            conn.request("GET" if body is None else "POST",
                         o.path,
                         body,
                         header)
    except socket.timeout as e:
        raise IMException(e)
    except OSError as e:
        raise IMException(e.strerror)

    try:
        res = conn.getresponse()
        size = int(res.getheader("Content-Length", 524288))
        cntype = res.getheader("Content-Type")

        if size > max_size or (cntype is not None and cntype[:4] != "text" and cntype[:4] != "appl"):
            raise IMException("Content too large to be retrieved")

        data = res.read(size)

        # Decode content
        charset = "utf-8"
        if cntype is not None:
            lcharset = res.getheader("Content-Type").split(";")
            if len(lcharset) > 1:
                for c in lcharset:
                    ch = c.split("=")
                    if ch[0].strip().lower() == "charset" and len(ch) > 1:
                        cha = ch[1].split(".")
                        if len(cha) > 1:
                            charset = cha[1]
                        else:
                            charset = cha[0]
    except http.client.BadStatusLine:
        raise IMException("Invalid HTTP response")
    finally:
        conn.close()

    if res.status == http.client.OK or res.status == http.client.SEE_OTHER:
        return data.decode(charset).strip()
    elif ((res.status == http.client.FOUND or
           res.status == http.client.MOVED_PERMANENTLY) and
          res.getheader("Location") != url):
        return getURLContent(
            urljoin(url, res.getheader("Location")),
            body=body,
            timeout=timeout,
            header=header,
            decode_error=decode_error,
            max_size=max_size)
    elif decode_error:
        return data.decode(charset).strip()
    else:
        raise IMException("A HTTP error occurs: %d - %s" %
                           (res.status, http.client.responses[res.status]))


def getXML(*args, **kwargs):
    """Get content page and return XML parsed content

    Arguments: same as getURLContent
    """

    cnt = getURLContent(*args, **kwargs)
    if cnt is None:
        return None
    else:
        from xml.dom.minidom import parseString
        return parseString(cnt)


def getJSON(*args, remove_callback=False, **kwargs):
    """Get content page and return JSON content

    Arguments: same as getURLContent
    """

    cnt = getURLContent(*args, **kwargs)
    if cnt is None:
        return None
    else:
        import json
        if remove_callback:
            import re
            cnt = re.sub(r"^[^(]+\((.*)\)$", r"\1", cnt)
        return json.loads(cnt)


# Other utils

def striphtml(data):
    """Remove HTML tags from text

    Argument:
    data -- the string to strip
    """

    if not isinstance(data, str) and not isinstance(data, bytes):
        return data

    try:
        from html import unescape
    except ImportError:
        def _replace_charref(s):
            s = s.group(1)

            if s[0] == '#':
                if s[1] in 'xX':
                    return chr(int(s[2:], 16))
                else:
                    return chr(int(s[2:]))
            else:
                from html.entities import name2codepoint
                return chr(name2codepoint[s])

        # unescape exists from Python 3.4
        def unescape(s):
            if '&' not in s:
                return s

            import re

            return re.sub('&([^;]+);', _replace_charref, s)


    import re
    return re.sub(r' +', ' ',
                  unescape(re.sub(r'<.*?>', '', data)).replace('\n', ' '))
