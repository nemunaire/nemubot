import json
import urllib

from nemubot import __version__
from nemubot.exception import IRCException

def validator(url):
    """Run the w3c validator on the given URL

    Argument:
    url -- the URL to validate
    """

    o = urllib.parse.urlparse(url, "http")
    if o.netloc == "":
        raise IRCException("Indicate a valid URL!")

    try:
        req = urllib.request.Request("http://validator.w3.org/check?uri=%s&output=json" % (urllib.parse.quote(o.geturl())), headers={ 'User-Agent' : "Nemubot v%s" % __version__})
        raw = urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as e:
        raise IRCException("HTTP error occurs: %s %s" % (e.code, e.reason))

    headers = dict()
    for Hname, Hval in raw.getheaders():
        headers[Hname] = Hval

    if "X-W3C-Validator-Status" not in headers or (headers["X-W3C-Validator-Status"] != "Valid" and headers["X-W3C-Validator-Status"] != "Invalid"):
        raise IRCException("Unexpected error on W3C servers" + (" (" + headers["X-W3C-Validator-Status"] + ")" if "X-W3C-Validator-Status" in headers else ""))

    return headers, json.loads(raw.read().decode())
