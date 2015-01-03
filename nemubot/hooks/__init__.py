# -*- coding: utf-8 -*-

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

import imp

from nemubot.exception import IRCException


def call_game(call, *args, **kargs):
    """TODO"""
    l = list()
    d = kargs

    for a in args:
        if a is not None:
            if isinstance(a, dict):
                d.update(a)
            else:
                l.append(a)

    return call(*l, **d)


class AbstractHook:

    """Abstract class for Hook implementation"""

    def __init__(self, call, data=None, mtimes=-1, end_call=None):
        self.call = call
        self.data = data

        self.times = mtimes
        self.end_call = end_call


    def match(self, data1, server):
        return NotImplemented


    def run(self, data1, *args):
        """Run the hook"""
        self.times -= 1

        try:
            ret = call_game(self.call, data1, self.data, *args)
        except IRCException as e:
            ret = e.fill_response(data1)
        finally:
            if self.times == 0:
                self.call_end(ret)

        return ret


from nemubot.hooks.messagehook import MessageHook

last_registered = []


def hook(store, *args, **kargs):
    """Function used as a decorator for module loading"""
    def sec(call):
        last_registered.append((store, MessageHook(call, *args, **kargs)))
        return call
    return sec


def reload():
    import nemubot.hooks.manager
    imp.reload(nemubot.hooks.manager)

    import nemubot.hooks.messagehook
    imp.reload(nemubot.hooks.messagehook)
