"""DNS resolver"""

# PYTHON STUFFS #######################################################

import dns.rdtypes.ANY
import dns.rdtypes.IN
import dns.resolver

from nemubot.exception import IMException
from nemubot.hooks import hook

from more import Response


# MODULE INTERFACE ####################################################

@hook.command("dig")
def dig(msg):
    ltype = "A"
    ldomain = None
    for a in msg.args:
        if a in dns.rdtypes.IN.__all__ or a in dns.rdtypes.ANY.__all__:
            ltype = a
        else:
            ldomain = a

    if not ldomain:
        raise IMException("indicate a domain to resolve")

    answers = dns.resolver.query(ldomain, ltype)

    res = Response(channel=msg.channel, title=ldomain, count=" (%s others records)")
    for rdata in answers:
        res.append_message(type(rdata).__name__ + " " + rdata.to_text())

    return res
