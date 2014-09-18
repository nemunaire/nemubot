# coding=utf-8

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

from response import Response

class IRCException(Exception):

    def __init__(self, message, personnal=True):
        super(IRCException, self).__init__(message)
        self.message = message
        self.personnal = personnal

    def fill_response(self, msg):
        return Response(self.message, channel=msg.receivers, nick=(msg.nick if self.personnal else None))
