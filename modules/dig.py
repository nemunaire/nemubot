"""DNS resolver"""

# PYTHON STUFFS #######################################################

import ipaddress
import socket

import dns.exception
import dns.name
import dns.rdataclass
import dns.rdatatype
import dns.resolver

from nemubot.exception import IMException
from nemubot.hooks import hook

from nemubot.module.more import Response


# MODULE INTERFACE ####################################################

@hook.command("dig",
              help="Resolve domain name with a basic syntax similar to dig(1)")
def dig(msg):
    lclass = "IN"
    ltype = "A"
    ledns = None
    ltimeout = 6.0
    ldomain = None
    lnameservers = []
    lsearchlist = []
    loptions = []
    for a in msg.args:
        if a in dns.rdatatype._by_text:
            ltype = a
        elif a in dns.rdataclass._by_text:
            lclass = a
        elif a[0] == "@":
            try:
                lnameservers.append(str(ipaddress.ip_address(a[1:])))
            except ValueError:
                for r in socket.getaddrinfo(a[1:], 53, proto=socket.IPPROTO_UDP):
                    lnameservers.append(r[4][0])

        elif a[0:8] == "+domain=":
            lsearchlist.append(dns.name.from_unicode(a[8:]))
        elif a[0:6] == "+edns=":
            ledns = int(a[6:])
        elif a[0:6] == "+time=":
            ltimeout = float(a[6:])
        elif a[0] == "+":
            loptions.append(a[1:])
        else:
            ldomain = a

    if not ldomain:
        raise IMException("indicate a domain to resolve")

    resolv = dns.resolver.Resolver()
    if ledns:
        resolv.edns = ledns
    resolv.lifetime = ltimeout
    resolv.timeout = ltimeout
    resolv.flags = (
        dns.flags.QR | dns.flags.RA |
        dns.flags.AA if "aaonly" in loptions or "aaflag" in loptions else 0 |
        dns.flags.AD if "adflag" in loptions else 0 |
        dns.flags.CD if "cdflag" in loptions else 0 |
        dns.flags.RD if "norecurse" not in loptions else 0
    )
    if lsearchlist:
        resolv.search = lsearchlist
    else:
        resolv.search = [dns.name.from_text(".")]

    if lnameservers:
        resolv.nameservers = lnameservers

    try:
        answers = resolv.query(ldomain, ltype, lclass, tcp="tcp" in loptions)
    except dns.exception.DNSException as e:
        raise IMException(str(e))

    res = Response(channel=msg.channel, count=" (%s others entries)")
    for rdata in answers:
        res.append_message("%s %s %s %s %s" % (
            answers.qname.to_text(),
            answers.ttl if not "nottlid" in loptions else "",
            dns.rdataclass.to_text(answers.rdclass) if not "nocl" in loptions else "",
            dns.rdatatype.to_text(answers.rdtype),
            rdata.to_text())
        )

    return res
