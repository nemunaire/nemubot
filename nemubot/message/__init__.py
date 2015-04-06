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

from nemubot.message.abstract import Abstract
from nemubot.message.text import Text
from nemubot.message.directask import DirectAsk
from nemubot.message.command import Command
from nemubot.message.command import OwnerCommand


def reload():
    global Abstract, Text, DirectAsk, Command, OwnerCommand
    import imp

    import nemubot.message.abstract
    imp.reload(nemubot.message.abstract)
    Abstract = nemubot.message.abstract.Abstract
    imp.reload(nemubot.message.text)
    Text = nemubot.message.text.Text
    imp.reload(nemubot.message.directask)
    DirectAsk = nemubot.message.directask.DirectAsk
    imp.reload(nemubot.message.command)
    Command = nemubot.message.command.Command
    OwnerCommand = nemubot.message.command.OwnerCommand

    import nemubot.message.visitor
    imp.reload(nemubot.message.visitor)

    import nemubot.message.printer
    imp.reload(nemubot.message.printer)

    nemubot.message.printer.reload()
