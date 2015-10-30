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

from nemubot.hooks.message import Message

last_registered = []


def hook(store, *args, **kargs):
    """Function used as a decorator for module loading"""
    def sec(call):
        last_registered.append((store, Message(call, *args, **kargs)))
        return call
    return sec


def reload():
    global Message
    import imp

    import nemubot.hooks.abstract
    imp.reload(nemubot.hooks.abstract)

    import nemubot.hooks.message
    imp.reload(nemubot.hooks.message)
    Message = nemubot.hooks.message.Message

    import nemubot.hooks.manager
    imp.reload(nemubot.hooks.manager)
