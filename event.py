# -*- coding: utf-8 -*-

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

import threading

class ModuleEvent:
    def __init__(self, func, func_data, check, cmp_data, intervalle=60,
                 call=None, call_data=None, times=1):
        # What have we to check?
        self.func = func
        self.func_data = func_data

        # How detect a change?
        self.check = check
        if cmp_data is not None:
            self.cmp_data = cmp_data
        else:
            self.cmp_data = self.func(self.func_data)

        self.intervalle = intervalle

        # What should we call when
        self.call = call
        if call_data is not None:
            self.call_data = call_data
        else:
            self.call_data = func_data

        # How many times do this event?
        self.times = times


    def launch_check(self):
        d = self.func(self.func_data)
        #print ("do test with", d, self.cmp_data)
        if self.check(d, self.cmp_data):
            self.call(self.call_data)
            self.times -= 1
        self.run()

    def run(self):
        if self.times != 0:
            #print ("run timer")
            self.timer = threading.Timer(self.intervalle, self.launch_check)
            self.timer.start()
        #else:
            #print ("no more times")

    def stop(self):
        self.timer.cancel()
