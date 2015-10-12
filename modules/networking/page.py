import http.client
import socket
import subprocess
import tempfile
import urllib

from nemubot import __version__
from nemubot.exception import IRCException
from nemubot.tools import web


def load(CONF, add_hook):
    # TODO: check w3m exists
    pass


def headers(url):
    """Retrieve HTTP header for the given URL

    Argument:
    url -- the page URL to get header
    """

    o = urllib.parse.urlparse(url, "http")
    if o.netloc == "":
        raise IRCException("invalid URL")
    if o.scheme == "http":
        conn = http.client.HTTPConnection(o.hostname, port=o.port, timeout=5)
    else:
        conn = http.client.HTTPSConnection(o.hostname, port=o.port, timeout=5)
    try:
        conn.request("HEAD", o.path, None, {"User-agent":
                                            "Nemubot v%s" % __version__})
    except ConnectionError as e:
        raise IRCException(e.strerror)
    except socket.timeout:
        raise IRCException("request timeout")
    except socket.gaierror:
        print ("<tools.web> Unable to receive page %s from %s on %d."
               % (o.path, o.hostname, o.port if o.port is not None else 0))
        raise IRCException("an unexpected error occurs")

    try:
        res = conn.getresponse()
    except http.client.BadStatusLine:
        raise IRCException("An error occurs")
    finally:
        conn.close()

    return (res.version, res.status, res.reason, res.getheaders())


def _onNoneDefault():
    raise IRCException("An error occurs when trying to access the page")


def fetch(url, onNone=_onNoneDefault):
    """Retrieve the content of the given URL

    Argument:
    url -- the URL to fetch
    """

    try:
        req = web.getURLContent(url)
        if req is not None:
            return req
        else:
            if callable(onNone):
                return onNone()
            else:
                return None
    except ConnectionError as e:
        raise IRCException(e.strerror)
    except socket.timeout:
        raise IRCException("The request timeout when trying to access the page")
    except socket.error as e:
        raise IRCException(e.strerror)


def _render(cnt):
    """Render the page contained in cnt as HTML page"""
    if cnt is None:
        return None

    with tempfile.NamedTemporaryFile() as fp:
        fp.write(cnt.encode())

        args = ["w3m", "-T", "text/html", "-dump"]
        args.append(fp.name)
        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            return proc.stdout.read().decode()


def render(url, onNone=_onNoneDefault):
    """Use w3m to render the given url

    Argument:
    url -- the URL to render
    """

    return _render(fetch(url, onNone))


def traceURL(url, stack=None):
    """Follow redirections and return the redirections stack

    Argument:
    url -- the URL to trace
    """

    if stack is None:
        stack = list()
    stack.append(url)

    if len(stack) > 15:
        stack.append('stack overflow :(')
        return stack

    _, status, _, heads = headers(url)

    if status == http.client.FOUND or status == http.client.MOVED_PERMANENTLY or status == http.client.SEE_OTHER:
        for h, c in heads:
            if h == "Location":
                url = c
                if url in stack:
                    stack.append("loop on " + url)
                    return stack
                else:
                    return traceURL(url, stack)
    return stack
