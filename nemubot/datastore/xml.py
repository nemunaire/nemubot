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

        self.basedir = os.path.abspath(basedir)
        self.rotate = rotate
        self.nb_save = 0

        logger.info("Initiate XML datastore at %s, rotation %s",
                    self.basedir,
                    "enabled" if self.rotate else "disabled")


    def open(self):
        """Lock the directory"""

        if not os.path.isdir(self.basedir):
            logger.debug("Datastore directory not found, creating: %s", self.basedir)
            os.mkdir(self.basedir)

        lock_path = self._get_lock_file_path()
        logger.debug("Locking datastore directory via %s", lock_path)

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

        logger.info("Datastore successfuly opened at %s", self.basedir)
        return True


    def close(self):
        """Release a locked path"""

        if hasattr(self, "lock_file"):
            self.lock_file.close()
            lock_path = self._get_lock_file_path()
            if os.path.isdir(self.basedir) and os.path.exists(lock_path):
                os.unlink(lock_path)
            del self.lock_file
            logger.info("Datastore successfully closed at %s", self.basedir)
            return True
        else:
            logger.warn("Datastore not open/locked or lock file not found")
        return False


    def _get_data_file_path(self, module):
        """Get the path to the module data file"""

        return os.path.join(self.basedir, module + ".xml")


    def _get_lock_file_path(self):
        """Get the path to the datastore lock file"""

        return os.path.join(self.basedir, ".used_by_nemubot")


    def load(self, module, extendsTags={}):
        """Load data for the given module

        Argument:
        module -- the module name of data to load
        """

        logger.debug("Trying to load data for %s%s",
                     module,
                     (" with tags: " + ", ".join(extendsTags.keys())) if len(extendsTags) else "")

        data_file = self._get_data_file_path(module)

        def parse(path):
            from nemubot.tools.xmlparser import XMLParser
            from nemubot.datastore.nodes import basic as basicNodes
            from nemubot.datastore.nodes import python as pythonNodes
            from nemubot.message.command import Command

            d = {
                basicNodes.ListNode.serializetag: basicNodes.ListNode,
                basicNodes.DictNode.serializetag: basicNodes.DictNode,
                pythonNodes.IntNode.serializetag: pythonNodes.IntNode,
                pythonNodes.FloatNode.serializetag: pythonNodes.FloatNode,
                pythonNodes.StringNode.serializetag: pythonNodes.StringNode,
                Command.serializetag: Command,
            }
            d.update(extendsTags)

            p = XMLParser(d)
            return p.parse_file(path)

        # Try to load original file
        if os.path.isfile(data_file):
            try:
                return parse(data_file)
            except xml.parsers.expat.ExpatError:
                # Try to load from backup
                for i in range(10):
                    path = data_file + "." + str(i)
                    if os.path.isfile(path):
                        try:
                            cnt = parse(path)

                            logger.warn("Restoring data from backup: %s", path)

                            return cnt
                        except xml.parsers.expat.ExpatError:
                            continue

        # Default case: initialize a new empty datastore
        logger.warn("No data found in store for %s, creating new set", module)
        return Abstract.load(self, module)


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


    def _save_node(self, gen, node):
        from nemubot.datastore.nodes.generic import ParsingNode

        # First, get the serialized form of the node
        node = ParsingNode.serialize_node(node)

        assert node.tag is not None, "Undefined tag name"

        gen.startElement(node.tag, {k: str(node.attrs[k]) for k in node.attrs})

        gen.characters(node.content)

        for child in node.children:
            self._save_node(gen, child)

        gen.endElement(node.tag)


    def save(self, module, data):
        """Load data for the given module

        Argument:
        module -- the module name of data to load
        data -- the new data to save
        """

        path = self._get_data_file_path(module)
        logger.debug("Trying to save data for module %s in %s", module, path)

        if self.rotate:
            self._rotate(path)

        import tempfile
        _, tmpath = tempfile.mkstemp()
        with open(tmpath, "w") as f:
            import xml.sax.saxutils
            gen = xml.sax.saxutils.XMLGenerator(f, "utf-8")
            gen.startDocument()
            self._save_node(gen, data)
            gen.endDocument()

        # Atomic save
        import shutil
        shutil.move(tmpath, path)

        return True
