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

from nemubot.hooks.abstract import Abstract
from nemubot.hooks.command import Command
from nemubot.hooks.message import Message


class hook:

    last_registered = []


    def _add(store, h, *args, **kwargs):
        """Function used as a decorator for module loading"""
        def sec(call):
            hook.last_registered.append((store, h(call, *args, **kwargs)))
            return call
        return sec


    def add(store, *args, **kwargs):
        return hook._add(store, Abstract, *args, **kwargs)

    def ask(*args, store="in_DirectAsk", **kwargs):
        return hook._add(store, Message, *args, **kwargs)

    def command(*args, store="in_Command", **kwargs):
        return hook._add(store, Command, *args, **kwargs)

    def message(*args, store="in_Text", **kwargs):
        return hook._add(store, Message, *args, **kwargs)

    def post(*args, store="post", **kwargs):
        return hook._add(store, Abstract, *args, **kwargs)

    def pre(*args, store="pre", **kwargs):
        return hook._add(store, Abstract, *args, **kwargs)


def reload():
    import imp

    import nemubot.hooks.abstract
    imp.reload(nemubot.hooks.abstract)

    import nemubot.hooks.command
    imp.reload(nemubot.hooks.command)

    import nemubot.hooks.message
    imp.reload(nemubot.hooks.message)

    import nemubot.hooks.keywords
    imp.reload(nemubot.hooks.keywords)
    nemubot.hooks.keywords.reload()

    import nemubot.hooks.manager
    imp.reload(nemubot.hooks.manager)
