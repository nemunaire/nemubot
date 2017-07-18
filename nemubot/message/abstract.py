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

from datetime import datetime, timezone


class Abstract:

    """This class represents an abstract message"""

    def __init__(self, server=None, date=None, to=None, to_response=None, frm=None, frm_owner=False):
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

        self.frm_owner = frm_owner


    @property
    def to_response(self):
        if self._to_response is not None:
            return self._to_response
        else:
            return self.to


    @property
    def channel(self):
        # TODO: this is for legacy modules
        if self.to_response is not None and len(self.to_response) > 0:
            return self.to_response[0]
        else:
            return None

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
            "frm": self.frm,
            "frm_owner": self.frm_owner,
        }

        for w in without:
            if w in ret:
                del ret[w]

        return ret
