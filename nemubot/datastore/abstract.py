# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2016  Mercier Pierre-Olivier
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

class Abstract:

    """Abstract implementation of a module data store, that always return an
    empty set"""

    def new(self):
        """Initialize a new empty storage tree
        """

        from nemubot.tools.xmlparser import module_state
        return module_state.ModuleState("nemubotstate")

    def open(self):
        return

    def close(self):
        return

    def load(self, module):
        """Load data for the given module

        Argument:
        module -- the module name of data to load

        Return:
        The loaded data
        """

        return self.new()

    def save(self, module, data):
        """Load data for the given module

        Argument:
        module -- the module name of data to load
        data -- the new data to save

        Return:
        Saving status
        """

        return True

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()
