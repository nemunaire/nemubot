# coding=utf-8

"""Use MediaWiki API to get pages"""

import re
import urllib.parse

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

nemubotversion = 3.4

from nemubot.module.more import Response


# MEDIAWIKI REQUESTS ##################################################

def get_namespaces(site, ssl=False, path="/w/api.php"):
    # Built URL
    url = "http%s://%s%s?format=json&action=query&meta=siteinfo&siprop=namespaces" % (
        "s" if ssl else "", site, path)

    # Make the request
    data = web.getJSON(url)

    namespaces = dict()
    for ns in data["query"]["namespaces"]:
        namespaces[data["query"]["namespaces"][ns]["*"]] = data["query"]["namespaces"][ns]
    return namespaces


def get_raw_page(site, term, ssl=False, path="/w/api.php"):
    # Built URL
    url = "http%s://%s%s?format=json&redirects&action=query&prop=revisions&rvprop=content&titles=%s" % (
        "s" if ssl else "", site, path, urllib.parse.quote(term))

    # Make the request
    data = web.getJSON(url)

    for k in data["query"]["pages"]:
        try:
            return data["query"]["pages"][k]["revisions"][0]["*"]
        except:
            raise IMException("article not found")


def get_unwikitextified(site, wikitext, ssl=False, path="/w/api.php"):
    # Built URL
    url = "http%s://%s%s?format=json&action=expandtemplates&text=%s" % (
        "s" if ssl else "", site, path, urllib.parse.quote(wikitext))

    # Make the request
    data = web.getJSON(url)

    return data["expandtemplates"]["*"]


## Search

def opensearch(site, term, ssl=False, path="/w/api.php"):
    # Built URL
    url = "http%s://%s%s?format=json&action=opensearch&search=%s" % (
        "s" if ssl else "", site, path, urllib.parse.quote(term))

    # Make the request
    response = web.getJSON(url)

    if response is not None and len(response) >= 4:
        for k in range(len(response[1])):
            yield (response[1][k],
                   response[2][k],
                   response[3][k])


def search(site, term, ssl=False, path="/w/api.php"):
    # Built URL
    url = "http%s://%s%s?format=json&action=query&list=search&srsearch=%s&srprop=titlesnippet|snippet" % (
        "s" if ssl else "", site, path, urllib.parse.quote(term))

    # Make the request
    data = web.getJSON(url)

    if data is not None and "query" in data and "search" in data["query"]:
        for itm in data["query"]["search"]:
            yield (web.striphtml(itm["titlesnippet"].replace("<span class='searchmatch'>", "\x03\x02").replace("</span>", "\x03\x02")),
                   web.striphtml(itm["snippet"].replace("<span class='searchmatch'>", "\x03\x02").replace("</span>", "\x03\x02")))


# PARSING FUNCTIONS ###################################################

def get_model(cnt, model="Infobox"):
    for full in re.findall(r"(\{\{" + model + " .*?(?:\{\{.*?}}.*?)*}})", cnt, flags=re.DOTALL):
        return full[3 + len(model):-2].replace("\n", " ").strip()


def strip_model(cnt):
    # Strip models at begin: mostly useless
    cnt = re.sub(r"^(({{([^{]|\s|({{([^{]|\s|{{.*?}})*?}})*?)*?}}|\[\[([^[]|\s|\[\[.*?\]\])*?\]\])\s*)+", "", cnt, flags=re.DOTALL)

    # Remove new line from models
    for full in re.findall(r"{{.*?}}", cnt, flags=re.DOTALL):
        cnt = cnt.replace(full, full.replace("\n", " "), 1)

    # Remove new line after titles
    cnt, _ = re.subn(r"((?P<title>==+)\s*(.*?)\s*(?P=title))\n+", r"\1", cnt)

    # Strip HTML comments
    cnt = re.sub(r"<!--.*?-->", "", cnt, flags=re.DOTALL)

    # Strip ref
    cnt = re.sub(r"<ref.*?/ref>", "", cnt, flags=re.DOTALL)
    return cnt


def parse_wikitext(site, cnt, namespaces=dict(), **kwargs):
    for i, _, _, _ in re.findall(r"({{([^{]|\s|({{(.|\s|{{.*?}})*?}})*?)*?}})", cnt):
        cnt = cnt.replace(i, get_unwikitextified(site, i, **kwargs), 1)

    # Strip [[...]]
    for full, args, lnk in re.findall(r"(\[\[(.*?|)?([^|]*?)\]\])", cnt):
        ns = lnk.find(":")
        if lnk == "":
            cnt = cnt.replace(full, args[:-1], 1)
        elif ns > 0:
            namespace = lnk[:ns]
            if namespace in namespaces and namespaces[namespace]["canonical"] == "Category":
                cnt = cnt.replace(full, "", 1)
                continue
            cnt = cnt.replace(full, lnk, 1)
        else:
            cnt = cnt.replace(full, lnk, 1)

    # Strip HTML tags
    cnt = web.striphtml(cnt)

    return cnt


# FORMATING FUNCTIONS #################################################

def irc_format(cnt):
    cnt, _ = re.subn(r"(?P<title>==+)\s*(.*?)\s*(?P=title)", "\x03\x16" + r"\2" + " :\x03\x16 ", cnt)
    return cnt.replace("'''", "\x03\x02").replace("''", "\x03\x1f")


def parse_infobox(cnt):
    for v in cnt.split("|"):
        try:
            yield re.sub(r"^\s*([^=]*[^=\s])\s*=\s*(.+)\s*$", "\x03\x02" + r"\1" + ":\x03\x02 " + r"\2", v).replace("<br />", ", ").replace("<br/>", ", ").strip()
        except:
            yield re.sub(r"^\s+(.+)\s+$", "\x03\x02" + r"\1" + "\x03\x02", v).replace("<br />", ", ").replace("<br/>", ", ").strip()


def get_page(site, term, subpart=None, **kwargs):
    raw = get_raw_page(site, term, **kwargs)

    if subpart is not None:
        subpart = subpart.replace("_", " ")
        raw = re.sub(r"^.*(?P<title>==+)\s*(" + subpart + r")\s*(?P=title)", r"\1 \2 \1", raw, flags=re.DOTALL)

    return raw


# NEMUBOT #############################################################

def mediawiki_response(site, term, to, **kwargs):
    ns = get_namespaces(site, **kwargs)

    terms = term.split("#", 1)

    try:
        # Print the article if it exists
        return Response(strip_model(get_page(site, terms[0], subpart=terms[1] if len(terms) > 1 else None, **kwargs)),
                        line_treat=lambda line: irc_format(parse_wikitext(site, line, ns, **kwargs)),
                        channel=to)
    except:
        pass

    # Try looking at opensearch
    os = [x for x, _, _ in opensearch(site, terms[0], **kwargs)]
    print(os)
    # Fallback to global search
    if not len(os):
        os = [x for x, _ in search(site, terms[0], **kwargs) if x is not None and x != ""]
    return Response(os,
                    channel=to,
                    title="Article not found, would you mean")


@hook.command("mediawiki",
              help="Read an article on a MediaWiki",
              keywords={
                  "ssl": "query over https instead of http",
                  "path=PATH": "absolute path to the API",
              })
def cmd_mediawiki(msg):
    if len(msg.args) < 2:
        raise IMException("indicate a domain and a term to search")

    return mediawiki_response(msg.args[0],
                              " ".join(msg.args[1:]),
                              msg.to_response,
                              **msg.kwargs)


@hook.command("mediawiki_search",
              help="Search an article on a MediaWiki",
              keywords={
                  "ssl": "query over https instead of http",
                  "path=PATH": "absolute path to the API",
              })
def cmd_srchmediawiki(msg):
    if len(msg.args) < 2:
        raise IMException("indicate a domain and a term to search")

    res = Response(channel=msg.to_response, nomore="No more results", count=" (%d more results)")

    for r in search(msg.args[0], " ".join(msg.args[1:]), **msg.kwargs):
        res.append_message("%s: %s" % r)

    return res


@hook.command("mediawiki_infobox",
              help="Highlight information from an article on a MediaWiki",
              keywords={
                  "ssl": "query over https instead of http",
                  "path=PATH": "absolute path to the API",
              })
def cmd_infobox(msg):
    if len(msg.args) < 2:
        raise IMException("indicate a domain and a term to search")

    ns = get_namespaces(msg.args[0], **msg.kwargs)

    return Response(", ".join([x for x in parse_infobox(get_model(get_page(msg.args[0], " ".join(msg.args[1:]), **msg.kwargs), "Infobox"))]),
                    line_treat=lambda line: irc_format(parse_wikitext(msg.args[0], line, ns, **msg.kwargs)),
                    channel=msg.to_response)


@hook.command("wikipedia")
def cmd_wikipedia(msg):
    if len(msg.args) < 2:
        raise IMException("indicate a lang and a term to search")

    return mediawiki_response(msg.args[0] + ".wikipedia.org",
                              " ".join(msg.args[1:]),
                              msg.to_response)
