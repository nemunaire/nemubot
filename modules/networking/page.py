import http.client
import socket
import subprocess
import tempfile
import urllib

from tools import web


def load(CONF, add_hook):
    # check w3m exists
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
        conn = http.client.HTTPConnection(o.netloc, port=o.port, timeout=5)
    else:
        conn = http.client.HTTPSConnection(o.netloc, port=o.port, timeout=5)
    try:
        conn.request("HEAD", o.path, None, {"User-agent": "Nemubot v3"})
    except socket.timeout:
        raise IRCException("request timeout")
    except socket.gaierror:
        print ("<tools.web> Unable to receive page %s from %s on %d."
               % (o.path, o.netloc, o.port))
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
            if onNone is not None:
                return onNone()
            else:
                return None
    except socket.timeout:
        raise IRCException("The request timeout when trying to access the page")
    except socket.error as e:
        raise IRCException(e.strerror)


def render(url, onNone=_onNoneDefault):
    """Use w3m to render the given url

    Argument:
    url -- the URL to render
    """

    with tempfile.NamedTemporaryFile() as fp:
        cnt = fetch(url, onNone)
        if cnt is None:
            return None
        fp.write(cnt.encode())

        args = ["w3m", "-T", "text/html", "-dump"]
        args.append(fp.name)
        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            return proc.stdout.read().decode()


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

    _, status, _, headers = headers(url)

    if status == http.client.FOUND or status == http.client.MOVED_PERMANENTLY or status == http.client.SEE_OTHER:
        for h, c in headers:
            if h == "Location":
                url = c
                if url in stack:
                    stack.append("loop on " + url)
                    return stack
                else:
                    return traceURL(url, stack)
    return stack
