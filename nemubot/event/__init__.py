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

    def __init__(self, call=None, func=None, cmp=None, interval=60, offset=0, times=1):

        """Initialize the event

        Keyword arguments:
        call -- Function to call when the event is realized
        func -- Function called to check
        cmp -- Boolean function called to check changes or value to compare with
        interval -- Time in seconds between each check (default: 60)
        offset -- Time in seconds added to interval before the first check (default: 0)
        times -- Number of times the event has to be realized before being removed; -1 for no limit (default: 1)
        """

        # What have we to check?
        self.func = func

        # How detect a change?
        self.cmp = cmp

        # What should we call when?
        self.call = call

        # Store times
        if isinstance(offset, timedelta):
            self.offset = offset  # Time to wait before the first check
        else:
            self.offset = timedelta(seconds=offset)  # Time to wait before the first check
        if isinstance(interval, timedelta):
            self.interval = interval
        else:
            self.interval = timedelta(seconds=interval)
        self._end = None  # Cache

        # How many times do this event?
        self.times = times

    @property
    def current(self):
        """Return the date of the near check"""
        if self.times != 0:
            if self._end is None:
                self._end = datetime.now(timezone.utc) + self.offset + self.interval
            return self._end
        return None

    @property
    def next(self):
        """Return the date of the next check"""
        if self.times != 0:
            if self._end is None:
                return self.current
            elif self._end < datetime.now(timezone.utc):
                self._end += self.interval
            return self._end
        return None

    @property
    def time_left(self):
        """Return the time left before/after the near check"""
        if self.current is not None:
            return self.current - datetime.now(timezone.utc)
        return timedelta.max

    def check(self):
        """Run a check and realized the event if this is time"""

        # Get new data
        if self.func is not None:
            d_new = self.func()
        else:
            d_new = None

        # then compare with current data
        if self.cmp is None or (callable(self.cmp) and self.cmp(d_new)) or (not callable(self.cmp) and d_new != self.cmp):
            self.times -= 1

            # Call attended function
            if self.func is not None:
                self.call(d_new)
            else:
                self.call()
