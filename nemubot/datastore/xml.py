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

import os

from nemubot.datastore.abstract import Abstract
from nemubot.tools.xmlparser import parse_file


class XML(Abstract):

    """A concrete implementation of a data store that relies on XML files"""

    def __init__(self, basedir):
        self.basedir = basedir

    def open(self):
        """Lock the directory"""

        if os.path.isdir(self.basedir):
            lock_file = os.path.join(self.basedir, ".used_by_nemubot")
            if not os.path.exists(lock_file):
                with open(lock_file, 'w') as lf:
                    lf.write(str(os.getpid()))
                return True

            else:
                with open(lock_file, 'r') as lf:
                    pid = lf.readline()
                raise Exception("Data dir already locked, by PID %s" % pid)
        return False

    def close(self):
        """Release a locked path"""

        lock_file = os.path.join(self.basedir, ".used_by_nemubot")
        if os.path.isdir(self.basedir) and os.path.exists(lock_file):
            os.unlink(lock_file)
            return True
        return False

    def _get_data_file_path(self, module):
        """Get the path to the module data file"""

        return os.path.join(self.basedir, module + ".xml")

    def load(self, module):
        """Load data for the given module

        Argument:
        module -- the module name of data to load
        """

        data_file = self._get_data_file_path(module)
        if os.path.isfile(data_file):
            return parse_file(data_file)
        else:
            return Abstract.load(self, module)

    def save(self, module, data):
        """Load data for the given module

        Argument:
        module -- the module name of data to load
        data -- the new data to save
        """

        return data.save(self._get_data_file_path(module))
