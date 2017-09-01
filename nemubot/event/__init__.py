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

from datetime import datetime, timedelta, timezone


class ModuleEvent:

    """Representation of a event initiated by a bot module"""

    def __init__(self, call=None, cmp=None, interval=60, offset=0, times=1):

        """Initialize the event

        Keyword arguments:
        call -- Function to call when the event is realized
        cmp -- Boolean function called to check changes
        interval -- Time in seconds between each check (default: 60)
        offset -- Time in seconds added to interval before the first check (default: 0)
        times -- Number of times the event has to be realized before being removed; -1 for no limit (default: 1)
        """

        # How detect a change?
        self.cmp = cmp

        # What should we call when?
        self.call = call

        # Time to wait before the first check
        if isinstance(offset, timedelta):
            self.offset = offset
        else:
            self.offset = timedelta(seconds=offset)
        self.interval = timedelta(seconds=interval)
        self._next = None  # Cache

        # How many times do this event?
        self.times = times


    def start(self, loop):
        if self._next is None:
            self._next = loop.time() + self.offset.total_seconds() + self.interval.total_seconds()


    def schedule(self, end):
        self.interval = timedelta(seconds=0)
        self.offset = end - datetime.now(timezone.utc)


    def next(self):
        if self.times != 0:
            self._next += self.interval.total_seconds()
            return True
        return False


    def check(self):
        """Run a check and realized the event if this is time"""

        if self.cmp():
            self.times -= 1
            self.call()
