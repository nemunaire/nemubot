"""Search engine for IoT"""

# PYTHON STUFFS #######################################################

from datetime import datetime
import ipaddress
import urllib.parse

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from nemubot.module.more import Response


# GLOBALS #############################################################

BASEURL = "https://api.shodan.io/shodan/"


# LOADING #############################################################

def load(context):
    if not context.config or "apikey" not in context.config:
        raise ImportError("You need a Shodan API key in order to use this "
                          "module. Add it to the module configuration file:\n"
                          "<module name=\"shodan\" apikey=\"XXXXXXXXXXXXXXXX\" "
                          "/>\nRegister at https://account.shodan.io/register")


# MODULE CORE #########################################################

def host_lookup(ip):
    url = BASEURL + "host/" + urllib.parse.quote(ip) + "?" + urllib.parse.urlencode({'key': context.config["apikey"]})
    return web.getJSON(url)


def search_hosts(query):
    url = BASEURL + "host/search?" + urllib.parse.urlencode({'query': query, 'key': context.config["apikey"]})
    return web.getJSON(url, max_size=4194304)


def print_ssl(ssl):
    return (
        "SSL: " +
        " ".join([v for v in ssl["versions"] if v[0] != "-"]) +
        "; cipher used: " + ssl["cipher"]["name"] +
        ("; certificate: " + ssl["cert"]["sig_alg"] +
        " issued by: " + ssl["cert"]["issuer"]["CN"] +
        " expires on: " + str(datetime.strptime(ssl["cert"]["expires"], "%Y%m%d%H%M%SZ")) if "cert" in ssl else "")
    )

def print_service(svc):
    ip = ipaddress.ip_address(svc["ip_str"])
    return ((svc["ip_str"] if ip.version == 4 else "[%s]" % svc["ip_str"]) +
            ":{port}/{transport} ({module}):" +
            (" {os}" if svc["os"] else "") +
            (" {product}" if "product" in svc else "") +
            (" {version}" if "version" in svc else "") +
            (" {info}" if "info" in svc else "") +
            (" Vulns: " + ", ".join(svc["opts"]["vulns"]) if "opts" in svc and "vulns" in svc["opts"] else "") +
            (" " + print_ssl(svc["ssl"]) if "ssl" in svc else "") +
            (" \x03\x1D" + svc["data"].replace("\r\n", "\n").split("\n")[0] + "\x03\x1D" if "data" in svc else "") +
            (" " + svc["title"] if "title" in svc else "")
           ).format(module=svc["_shodan"]["module"], **svc)


# MODULE INTERFACE ####################################################

@hook.command("shodan",
              help="Use shodan.io to get information on machines connected to Internet",
              help_usage={
                  "IP": "retrieve information about the given IP (can be v4 or v6)",
                  "TERM": "retrieve all hosts matching TERM somewhere in their exposed stuff"
              })
def shodan(msg):
    if not msg.args:
        raise IMException("indicate an IP or a term to search!")

    terms = " ".join(msg.args)

    try:
        ip = ipaddress.ip_address(terms)
    except ValueError:
        ip = None

    if ip:
        h = host_lookup(terms)
        res = Response(channel=msg.channel,
                       title="%s" % ((h["ip_str"] if ip.version == 4 else "[%s]" % h["ip_str"]) + (" (" + ", ".join(h["hostnames"]) + ")") if h["hostnames"] else ""))
        res.append_message("{isp} ({asn}) -> {city} ({country_code}), running {os}. Vulns: {vulns_str}. Open ports: {open_ports}. Last update: {last_update}".format(
            open_ports=", ".join(map(lambda a: str(a), h["ports"])), vulns_str=", ".join(h["vulns"]) if "vulns" in h else None, **h).strip())
        for d in h["data"]:
            res.append_message(print_service(d))

    else:
        q = search_hosts(terms)
        res = Response(channel=msg.channel,
                       count=" (%%s/%s results)" % q["total"])
        for r in q["matches"]:
            res.append_message(print_service(r))

    return res
