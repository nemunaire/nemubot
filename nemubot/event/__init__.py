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

    def __init__(self, call=None, call_data=None, func=None, func_data=None,
                 cmp=None, cmp_data=None, interval=60, offset=0, times=1):

        """Initialize the event

        Keyword arguments:
        call -- Function to call when the event is realized
        call_data -- Argument(s) (single or dict) to pass as argument
        func -- Function called to check
        func_data -- Argument(s) (single or dict) to pass as argument OR if no func, initial data to watch
        cmp -- Boolean function called to check changes
        cmp_data -- Argument(s) (single or dict) to pass as argument OR if no cmp, data compared to previous
        interval -- Time in seconds between each check (default: 60)
        offset -- Time in seconds added to interval before the first check (default: 0)
        times -- Number of times the event has to be realized before being removed; -1 for no limit (default: 1)
        """

        # What have we to check?
        self.func = func
        self.func_data = func_data

        # How detect a change?
        self.cmp = cmp
        self.cmp_data = None
        if cmp_data is not None:
            self.cmp_data = cmp_data
        elif self.func is not None:
            if self.func_data is None:
                self.cmp_data = self.func()
            elif isinstance(self.func_data, dict):
                self.cmp_data = self.func(**self.func_data)
            else:
                self.cmp_data = self.func(self.func_data)

        # What should we call when?
        self.call = call
        if call_data is not None:
            self.call_data = call_data
        else:
            self.call_data = func_data

        # Store times
        self.offset = timedelta(seconds=offset)  # Time to wait before the first check
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

        # Get initial data
        if self.func is None:
            d_init = self.func_data
        elif self.func_data is None:
            d_init = self.func()
        elif isinstance(self.func_data, dict):
            d_init = self.func(**self.func_data)
        else:
            d_init = self.func(self.func_data)

        # then compare with current data
        if self.cmp is None:
            if self.cmp_data is None:
                rlz = True
            else:
                rlz = (d_init != self.cmp_data)
        elif self.cmp_data is None:
            rlz = self.cmp(d_init)
        elif isinstance(self.cmp_data, dict):
            rlz = self.cmp(d_init, **self.cmp_data)
        else:
            rlz = self.cmp(d_init, self.cmp_data)

        if rlz:
            self.times -= 1

            # Call attended function
            if self.call_data is None:
                if d_init is None:
                    self.call()
                else:
                    self.call(d_init)
            elif isinstance(self.call_data, dict):
                self.call(d_init, **self.call_data)
            elif d_init is None:
                self.call(self.call_data)
            else:
                self.call(d_init, self.call_data)
