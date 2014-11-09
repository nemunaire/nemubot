# -*- coding: utf-8 -*-

# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2014  nemunaire
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

from datetime import datetime, timezone
import imp


class AbstractMessage:

    """This class represents an abstract message"""

    def __init__(self, server, date=None, to=None, to_response=None, frm=None):
        """Initialize an abstract message

        Arguments:
        server -- the servir identifier
        date -- time of the message reception, default: now
        to -- list of recipients
        to_response -- if channel(s) where send the response differ
        frm -- the sender
        """

        self.server = server
        self.date = datetime.now(timezone.utc) if date is None else date
        self.to = to if to is not None else list()
        self._to_response = (to_response if (to_response is None or
                                             isinstance(to_response, list))
                             else [ to_response ])
        self.frm = frm  # None allowed when it designate this bot

        self.frm_owner = False  # Filled later, in consumer


    @property
    def to_response(self):
        if self._to_response is not None:
            return self._to_response
        else:
            return self.to


    @property
    def receivers(self):
        # TODO: this is for legacy modules
        return self.to_response

    @property
    def channel(self):
        # TODO: this is for legacy modules
        return self.to_response[0]

    @property
    def nick(self):
        # TODO: this is for legacy modules
        return self.frm


    def accept(self, visitor):
        visitor.visit(self)


    def export_args(self, without=list()):
        if not isinstance(without, list):
            without = [ without ]

        ret = {
            "server": self.server,
            "date": self.date,
            "to": self.to,
            "to_response": self._to_response,
            "frm": self.frm
        }

        for w in without:
            if w in ret:
                del ret[w]

        return ret


class TextMessage(AbstractMessage):

    """This class represent a simple message send to someone"""

    def __init__(self, message, *args, **kargs):
        """Initialize a message with no particular specificity

        Argument:
        message -- the parsed message
        """

        AbstractMessage.__init__(self, *args, **kargs)

        self.message = message

    def __str__(self):
        return self.message

    @property
    def text(self):
        # TODO: this is for legacy modules
        return self.message


class DirectAsk(TextMessage):

    """This class represents a message to this bot"""

    def __init__(self, designated, *args, **kargs):
        """Initialize a message to a specific person

        Argument:
        designated -- the user designated by the message
        """

        TextMessage.__init__(self, *args, **kargs)

        self.designated = designated

    def respond(self, message):
        return DirectAsk(self.frm,
                         message,
                         server=self.server,
                         to=self.to_response)


class Command(AbstractMessage):

    """This class represents a specialized TextMessage"""

    def __init__(self, cmd, args=None, *nargs, **kargs):
        AbstractMessage.__init__(self, *nargs, **kargs)

        self.cmd = cmd
        self.args = args if args is not None else list()

    def __str__(self):
        return self.cmd + " @" + ",@".join(self.args)

    @property
    def cmds(self):
        # TODO: this is for legacy modules
        return [self.cmd] + self.args


class OwnerCommand(Command):

    """This class represents a special command incomming from the owner"""

    pass


def reload():
    import message.visitor
    imp.reload(message.visitor)

    import message.printer
    imp.reload(message.printer)

    message.printer.reload()
