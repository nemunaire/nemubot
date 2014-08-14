# -*- coding: utf-8 -*-

# Nemubot is a modulable IRC bot, built around XML configuration files.
# Copyright (C) 2012  Mercier Pierre-Olivier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import imp
import os
import shlex
import sys
import traceback

from . import builtins

class Prompt:
    def __init__(self, hc=dict(), hl=dict()):
        self.selectedServer = None

        self.HOOKS_CAPS = hc
        self.HOOKS_LIST = hl

    def add_cap_hook(self, name, call, data=None):
        self.HOOKS_CAPS[name] = (lambda d, t, c, p: call(d, t, c, p), data)


    def lex_cmd(self, line):
        """Return an array of tokens"""
        ret = list()
        try:
            cmds = shlex.split(line)
            bgn = 0
            for i in range(0, len(cmds)):
                if cmds[i] == ';':
                    if i != bgn:
                        cmds[bgn] = cmds[bgn].lower()
                        ret.append(cmds[bgn:i])
                    bgn = i + 1

            if bgn != len(cmds):
                cmds[bgn] = cmds[bgn].lower()
                ret.append(cmds[bgn:len(cmds)])

            return ret
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            sys.stderr.write (traceback.format_exception_only(
                    exc_type, exc_value)[0])
        return ret

    def exec_cmd(self, toks, context):
        """Execute the command"""
        if toks[0] in builtins.CAPS:
            return builtins.CAPS[toks[0]](toks, context, self)
        elif toks[0] in self.HOOKS_CAPS:
            (f,d) = self.HOOKS_CAPS[toks[0]]
            return f(d, toks, context, self)
        else:
            print("Unknown command: `%s'" % toks[0])
            return ""

    def getPS1(self):
        """Get the PS1 associated to the selected server"""
        if self.selectedServer is None:
            return "nemubot"
        else:
            return self.selectedServer.id

    def run(self, context):
        """Launch the prompt"""
        ret = ""
        while ret != "quit" and ret != "reset" and ret != "refresh":
            sys.stdout.write("\033[0;33m%s§\033[0m " % self.getPS1())
            sys.stdout.flush()

            try:
                line = sys.stdin.readline()
                if len(line) <= 0:
                    line = "quit"
                    print("quit")
                cmds = self.lex_cmd(line.strip())
                for toks in cmds:
                    try:
                        ret = self.exec_cmd(toks, context)
                    except:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        traceback.print_exception(exc_type, exc_value, exc_traceback)
            except KeyboardInterrupt:
                print("")
        return ret != "quit"


def hotswap(prompt):
    return Prompt(prompt.HOOKS_CAPS, prompt.HOOKS_LIST)
