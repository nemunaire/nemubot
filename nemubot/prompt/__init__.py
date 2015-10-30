# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2015  Mercier Pierre-Olivier
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

import shlex
import sys
import traceback

from nemubot.prompt import builtins


class Prompt:

    def __init__(self):
        self.selectedServer = None
        self.lastretcode = 0

        self.HOOKS_CAPS = dict()
        self.HOOKS_LIST = dict()

    def add_cap_hook(self, name, call, data=None):
        self.HOOKS_CAPS[name] = lambda t, c: call(t, data=data,
                                                  context=c, prompt=self)

    def add_list_hook(self, name, call):
        self.HOOKS_LIST[name] = call

    def lex_cmd(self, line):
        """Return an array of tokens

        Argument:
        line -- the line to lex
        """

        try:
            cmds = shlex.split(line)
        except:
            exc_type, exc_value, _ = sys.exc_info()
            sys.stderr.write(traceback.format_exception_only(exc_type,
                                                             exc_value)[0])
            return

        bgn = 0

        # Separate commands (command separator: ;)
        for i in range(0, len(cmds)):
            if cmds[i][-1] == ';':
                if i != bgn:
                    yield cmds[bgn:i]
                bgn = i + 1

        # Return rest of the command (that not end with a ;)
        if bgn != len(cmds):
            yield cmds[bgn:]

    def exec_cmd(self, toks, context):
        """Execute the command

        Arguments:
        toks -- lexed tokens to executes
        context -- current bot context
        """

        if toks[0] in builtins.CAPS:
            self.lastretcode = builtins.CAPS[toks[0]](toks, context, self)
        elif toks[0] in self.HOOKS_CAPS:
            self.lastretcode = self.HOOKS_CAPS[toks[0]](toks, context)
        else:
            print("Unknown command: `%s'" % toks[0])
            self.lastretcode = 127

    def getPS1(self):
        """Get the PS1 associated to the selected server"""
        if self.selectedServer is None:
            return "nemubot"
        else:
            return self.selectedServer.id

    def run(self, context):
        """Launch the prompt

        Argument:
        context -- current bot context
        """

        from nemubot.prompt.error import PromptError
        from nemubot.prompt.reset import PromptReset

        while True:  # Stopped by exception
            try:
                line = input("\033[0;33m%s\033[0;%dm§\033[0m " %
                             (self.getPS1(), 31 if self.lastretcode else 32))
                cmds = self.lex_cmd(line.strip())
                for toks in cmds:
                    try:
                        self.exec_cmd(toks, context)
                    except PromptReset:
                        raise
                    except PromptError as e:
                        print(e.message)
                        self.lastretcode = 128
                    except:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        traceback.print_exception(exc_type, exc_value,
                                                  exc_traceback)
            except KeyboardInterrupt:
                print("")
            except EOFError:
                print("quit")
                return True


def hotswap(bak):
    p = Prompt()
    p.HOOKS_CAPS = bak.HOOKS_CAPS
    p.HOOKS_LIST = bak.HOOKS_LIST
    return p


def reload():
    import imp

    import nemubot.prompt.builtins
    imp.reload(nemubot.prompt.builtins)

    import nemubot.prompt.error
    imp.reload(nemubot.prompt.error)

    import nemubot.prompt.reset
    imp.reload(nemubot.prompt.reset)
