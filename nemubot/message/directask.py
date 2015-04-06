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

from nemubot.message.text import Text


class DirectAsk(Text):

    """This class represents a message to this bot"""

    def __init__(self, designated, *args, **kargs):
        """Initialize a message to a specific person

        Argument:
        designated -- the user designated by the message
        """

        Text.__init__(self, *args, **kargs)

        self.designated = designated

    def respond(self, message):
        return DirectAsk(self.frm,
                         message,
                         server=self.server,
                         to=self.to_response)
