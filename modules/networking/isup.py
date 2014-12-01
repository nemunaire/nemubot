import json
import urllib


def isup(url):
    """Determine if the given URL is up or not

    Argument:
    url -- the URL to check
    """

    o = urllib.parse.urlparse(url, "http")
    if o.netloc == "":
        o = urllib.parse.urlparse("http://" + url)
    if o.netloc != "":
        req = urllib.request.Request("http://isitup.org/%s.json" % (o.netloc), headers={ 'User-Agent' : "nemubot v3" })
        raw = urllib.request.urlopen(req, timeout=10)
        isup = json.loads(raw.read().decode())
        if "status_code" in isup and isup["status_code"] == 1:
            return isup["response_time"]

    return None
