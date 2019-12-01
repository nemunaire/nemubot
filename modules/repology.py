# coding=utf-8

"""Repology.org module: the packaging hub"""

import datetime
import re

from nemubot import context
from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web
from nemubot.tools.xmlparser.node import ModuleState

nemubotversion = 4.0

from nemubot.module.more import Response

URL_REPOAPI = "https://repology.org/api/v1/project/%s"

def get_json_project(project):
    prj = web.getJSON(URL_REPOAPI % (project))

    return prj


@hook.command("repology",
              help="Display version information about a package",
              help_usage={
                  "PACKAGE_NAME": "Retrieve informations about PACKAGE_NAME",
              },
              keywords={
                  "distro=DISTRO": "filter by disto",
                  "status=STATUS[,STATUS...]": "filter by status",
              })
def cmd_repology(msg):
    if len(msg.args) == 0:
        raise IMException("Please provide at least a package name")

    res = Response(channel=msg.channel, nomore="No more information on package")

    for project in msg.args:
        prj = get_json_project(project)
        if len(prj) == 0:
            raise IMException("Unable to find package " + project)

        pkg_versions = {}
        pkg_maintainers = {}
        pkg_licenses = {}
        summary = None

        for repo in prj:
            # Apply filters
            if "distro" in msg.kwargs and repo["repo"].find(msg.kwargs["distro"]) < 0:
                continue
            if "status" in msg.kwargs and repo["status"] not in msg.kwargs["status"].split(","):
                continue

            name = repo["visiblename"] if "visiblename" in repo else repo["name"]
            status = repo["status"] if "status" in repo else "unknown"
            if name not in pkg_versions:
                pkg_versions[name] = {}
            if status not in pkg_versions[name]:
                pkg_versions[name][status] = []
            if repo["version"] not in pkg_versions[name][status]:
                pkg_versions[name][status].append(repo["version"])

            if "maintainers" in repo:
                if name not in pkg_maintainers:
                    pkg_maintainers[name] = []
                for maintainer in repo["maintainers"]:
                    if maintainer not in pkg_maintainers[name]:
                        pkg_maintainers[name].append(maintainer)

            if "licenses" in repo:
                if name not in pkg_licenses:
                    pkg_licenses[name] = []
                for lic in repo["licenses"]:
                    if lic not in pkg_licenses[name]:
                        pkg_licenses[name].append(lic)

            if "summary" in repo and summary is None:
                summary = repo["summary"]

        for pkgname in sorted(pkg_versions.keys()):
            m = "Package " + pkgname + " (" + summary + ")"
            if pkgname in pkg_licenses:
                m += " under " + ", ".join(pkg_licenses[pkgname])
            m += ": " + " - ".join([status + ": " + ", ".join(pkg_versions[pkgname][status]) for status in ["newest", "devel", "unique", "outdated", "legacy", "rolling", "noscheme", "untrusted", "ignored"] if status in pkg_versions[pkgname]])
            if "distro" in msg.kwargs and pkgname in pkg_maintainers:
                m += " - Maintained by " + ", ".join(pkg_maintainers[pkgname])

            res.append_message(m)

    return res
