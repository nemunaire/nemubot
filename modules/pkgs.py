"""Get information about common software"""

# PYTHON STUFFS #######################################################

import portage

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook

from more import Response

DB = None

# MODULE CORE #########################################################

def get_db():
    global DB
    if DB is None:
        DB = portage.db[portage.root]["porttree"].dbapi
    return DB


def package_info(pkgname):
    pv = get_db().xmatch("match-all", pkgname)
    if not pv:
        raise IMException("No package named '%s' found" % pkgname)

    bv = get_db().xmatch("bestmatch-visible", pkgname)
    pvsplit = portage.catpkgsplit(bv if bv else pv[-1])
    info = get_db().aux_get(bv if bv else pv[-1], ["DESCRIPTION", "HOMEPAGE", "LICENSE", "IUSE", "KEYWORDS"])

    return {
        "pkgname": '/'.join(pvsplit[:2]),
        "category": pvsplit[0],
        "shortname": pvsplit[1],
        "lastvers": '-'.join(pvsplit[2:]) if pvsplit[3] != "r0" else pvsplit[2],
        "othersvers": ['-'.join(portage.catpkgsplit(p)[2:]) for p in pv if p != bv],
        "description": info[0],
        "homepage": info[1],
        "license": info[2],
        "uses": info[3],
        "keywords": info[4],
    }


# MODULE INTERFACE ####################################################

@hook.command("eix",
      help="Get information about a package",
      help_usage={
          "NAME": "Get information about a software NAME"
      })
def cmd_eix(msg):
    if not len(msg.args):
        raise IMException("please give me a package to search")

    def srch(term):
        try:
            yield package_info(term)
        except portage.exception.AmbiguousPackageName as e:
            for i in e.args[0]:
                yield package_info(i)

    res = Response(channel=msg.channel, count=" (%d more packages)", nomore="No more package '%s'" % msg.args[0])
    for pi in srch(msg.args[0]):
        res.append_message("\x03\x02{pkgname}:\x03\x02 {description} - {homepage} - {license} - last revisions: \x03\x02{lastvers}\x03\x02{ov}".format(ov=(", " + ', '.join(pi["othersvers"])) if pi["othersvers"] else "", **pi))
    return res
