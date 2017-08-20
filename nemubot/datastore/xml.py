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

import fcntl
import logging
import os
import xml.parsers.expat

from nemubot.datastore.abstract import Abstract

logger = logging.getLogger("nemubot.datastore.xml")


class XML(Abstract):

    """A concrete implementation of a data store that relies on XML files"""

    def __init__(self, basedir, rotate=True):
        """Initialize the datastore

        Arguments:
        basedir -- path to directory containing XML files
        rotate -- auto-backup files?
        """

        self.basedir = basedir
        self.rotate = rotate
        self.nb_save = 0

    def open(self):
        """Lock the directory"""

        if not os.path.isdir(self.basedir):
            os.mkdir(self.basedir)

        lock_path = os.path.join(self.basedir, ".used_by_nemubot")

        self.lock_file = open(lock_path, 'a+')
        ok = True
        try:
            fcntl.lockf(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            ok = False

        if not ok:
            with open(lock_path, 'r') as lf:
                pid = lf.readline()
            raise Exception("Data dir already locked, by PID %s" % pid)

        self.lock_file.truncate()
        self.lock_file.write(str(os.getpid()))
        self.lock_file.flush()

        return True

    def close(self):
        """Release a locked path"""

        if hasattr(self, "lock_file"):
            self.lock_file.close()
            lock_path = os.path.join(self.basedir, ".used_by_nemubot")
            if os.path.isdir(self.basedir) and os.path.exists(lock_path):
                os.unlink(lock_path)
            del self.lock_file
            return True
        return False

    def _get_data_file_path(self, module):
        """Get the path to the module data file"""

        return os.path.join(self.basedir, module + ".xml")

    def load(self, module, knodes):
        """Load data for the given module

        Argument:
        module -- the module name of data to load
        knodes -- the schema to use to load the datas
        """

        data_file = self._get_data_file_path(module)

        if knodes is None:
            from nemubot.tools.xmlparser import parse_file
            def _true_load(path):
                return parse_file(path)

        else:
            from nemubot.tools.xmlparser import XMLParser
            p = XMLParser(knodes)
            def _true_load(path):
                return p.parse_file(path)

        # Try to load original file
        if os.path.isfile(data_file):
            try:
                return _true_load(data_file)
            except xml.parsers.expat.ExpatError:
                # Try to load from backup
                for i in range(10):
                    path = data_file + "." + str(i)
                    if os.path.isfile(path):
                        try:
                            cnt = _true_load(path)

                            logger.warn("Restoring from backup: %s", path)

                            return cnt
                        except xml.parsers.expat.ExpatError:
                            continue

        # Default case: initialize a new empty datastore
        return super().load(module, knodes)

    def _rotate(self, path):
        """Backup given path

        Argument:
        path -- location of the file to backup
        """

        self.nb_save += 1

        for i in range(10):
            if self.nb_save % (1 << i) == 0:
                src = path + "." + str(i-1) if i != 0 else path
                dst = path + "." + str(i)
                if os.path.isfile(src):
                    os.rename(src, dst)

    def save(self, module, data):
        """Load data for the given module

        Argument:
        module -- the module name of data to load
        data -- the new data to save
        """

        path = self._get_data_file_path(module)

        if self.rotate:
            self._rotate(path)

        if data is None:
            return

        import tempfile
        _, tmpath = tempfile.mkstemp()
        with open(tmpath, "w") as f:
            import xml.sax.saxutils
            gen = xml.sax.saxutils.XMLGenerator(f, "utf-8")
            gen.startDocument()
            data.saveElement(gen)
            gen.endDocument()

        # Atomic save
        import shutil
        shutil.move(tmpath, path)
