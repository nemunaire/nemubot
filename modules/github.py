"""Repositories, users or issues on GitHub"""

# PYTHON STUFFS #######################################################

import re
from urllib.parse import quote

from nemubot.exception import IMException
from nemubot.hooks import hook
from nemubot.tools import web

from nemubot.module.more import Response


# MODULE CORE #########################################################

def info_repos(repo):
    return web.getJSON("https://api.github.com/search/repositories?q=%s" %
                       quote(repo))


def info_user(username):
    user = web.getJSON("https://api.github.com/users/%s" % quote(username))

    user["repos"] = web.getJSON("https://api.github.com/users/%s/"
                                "repos?sort=updated" % quote(username))

    return user


def user_keys(username):
    keys = web.getURLContent("https://github.com/%s.keys" % quote(username))
    return keys.split('\n')


def info_issue(repo, issue=None):
    rp = info_repos(repo)
    if rp["items"]:
        fullname = rp["items"][0]["full_name"]
    else:
        fullname = repo

    if issue is not None:
        return [web.getJSON("https://api.github.com/repos/%s/issues/%s" %
                            (quote(fullname), quote(issue)))]
    else:
        return web.getJSON("https://api.github.com/repos/%s/issues?"
                           "sort=updated" % quote(fullname))


def info_commit(repo, commit=None):
    rp = info_repos(repo)
    if rp["items"]:
        fullname = rp["items"][0]["full_name"]
    else:
        fullname = repo

    if commit is not None:
        return [web.getJSON("https://api.github.com/repos/%s/commits/%s" %
                            (quote(fullname), quote(commit)))]
    else:
        return web.getJSON("https://api.github.com/repos/%s/commits" %
                           quote(fullname))


# MODULE INTERFACE ####################################################

@hook.command("github",
              help="Display information about some repositories",
              help_usage={
                  "REPO": "Display information about the repository REPO",
              })
def cmd_github(msg):
    if not len(msg.args):
        raise IMException("indicate a repository name to search")

    repos = info_repos(" ".join(msg.args))

    res = Response(channel=msg.channel,
                   nomore="No more repository",
                   count=" (%d more repo)")

    for repo in repos["items"]:
        homepage = ""
        if repo["homepage"] is not None:
            homepage = repo["homepage"] + " - "
        res.append_message("Repository %s: %s%s Main language: %s; %d forks; %d stars; %d watchers; %d opened_issues; view it at %s" %
                           (repo["full_name"],
                            homepage,
                            repo["description"],
                            repo["language"], repo["forks"],
                            repo["stargazers_count"],
                            repo["watchers_count"],
                            repo["open_issues_count"],
                            repo["html_url"]))

    return res


@hook.command("github_user",
              help="Display information about users",
              help_usage={
                  "USERNAME": "Display information about the user USERNAME",
              })
def cmd_github_user(msg):
    if not len(msg.args):
        raise IMException("indicate a user name to search")

    res = Response(channel=msg.channel, nomore="No more user")

    user = info_user(" ".join(msg.args))

    if "login" in user:
        if user["repos"]:
            kf = (" Known for: " +
                  ", ".join([repo["name"] for repo in user["repos"]]))
        else:
            kf = ""
        if "name" in user:
            name = user["name"]
        else:
            name = user["login"]
        res.append_message("User %s: %d public repositories; %d public gists; %d followers; %d following; view it at %s.%s" %
                           (name,
                            user["public_repos"],
                            user["public_gists"],
                            user["followers"],
                            user["following"],
                            user["html_url"],
                            kf))
    else:
        raise IMException("User not found")

    return res


@hook.command("github_user_keys",
              help="Display user SSH keys",
              help_usage={
                  "USERNAME": "Show USERNAME's SSH keys",
              })
def cmd_github_user_keys(msg):
    if not len(msg.args):
        raise IMException("indicate a user name to search")

    res = Response(channel=msg.channel, nomore="No more keys")

    for k in user_keys(" ".join(msg.args)):
        res.append_message(k)

    return res


@hook.command("github_issue",
              help="Display repository's issues",
              help_usage={
                  "REPO": "Display latest issues created on REPO",
                  "REPO #ISSUE": "Display the issue number #ISSUE for REPO",
              })
def cmd_github_issue(msg):
    if not len(msg.args):
        raise IMException("indicate a repository to view its issues")

    issue = None

    li = re.match("^#?([0-9]+)$", msg.args[0])
    ri = re.match("^#?([0-9]+)$", msg.args[-1])
    if li is not None:
        issue = li.group(1)
        del msg.args[0]
    elif ri is not None:
        issue = ri.group(1)
        del msg.args[-1]

    repo = " ".join(msg.args)

    count = " (%d more issues)" if issue is None else None
    res = Response(channel=msg.channel, nomore="No more issue", count=count)

    issues = info_issue(repo, issue)

    if issues is None:
        raise IMException("Repository not found")

    for issue in issues:
        res.append_message("%s%s issue #%d: \x03\x02%s\x03\x02 opened by %s on %s: %s" %
                           (issue["state"][0].upper(),
                            issue["state"][1:],
                            issue["number"],
                            issue["title"],
                            issue["user"]["login"],
                            issue["created_at"],
                            issue["body"].replace("\n", " ")))
    return res


@hook.command("github_commit",
              help="Display repository's commits",
              help_usage={
                  "REPO": "Display latest commits on REPO",
                  "REPO COMMIT": "Display details for the COMMIT on REPO",
              })
def cmd_github_commit(msg):
    if not len(msg.args):
        raise IMException("indicate a repository to view its commits")

    commit = None
    if re.match("^[a-fA-F0-9]+$", msg.args[0]):
        commit = msg.args[0]
        del msg.args[0]
    elif re.match("^[a-fA-F0-9]+$", msg.args[-1]):
        commit = msg.args[-1]
        del msg.args[-1]

    repo = " ".join(msg.args)

    count = " (%d more commits)" if commit is None else None
    res = Response(channel=msg.channel, nomore="No more commit", count=count)

    commits = info_commit(repo, commit)

    if commits is None:
        raise IMException("Repository or commit not found")

    for commit in commits:
        res.append_message("Commit %s by %s on %s: %s" %
                           (commit["sha"][:10],
                            commit["commit"]["author"]["name"],
                            commit["commit"]["author"]["date"],
                            commit["commit"]["message"].replace("\n", " ")))
    return res
