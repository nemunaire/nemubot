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

from importlib.abc import Finder
from importlib.machinery import SourceFileLoader
import logging
import os

logger = logging.getLogger("nemubot.importer")


class ModuleFinder(Finder):

    def __init__(self, modules_paths, add_module):
        self.modules_paths = modules_paths
        self.add_module = add_module

    def find_module(self, fullname, path=None):
        if path is not None and fullname.startswith("nemubot.module."):
            module_name = fullname.split(".", 2)[2]
            for mpath in self.modules_paths:
                if os.path.isfile(os.path.join(mpath, module_name + ".py")):
                    return ModuleLoader(self.add_module, fullname,
                                        os.path.join(mpath, module_name + ".py"))
                elif os.path.isfile(os.path.join(os.path.join(mpath, module_name), "__init__.py")):
                    return ModuleLoader(self.add_module, fullname,
                                        os.path.join(
                                            os.path.join(mpath, module_name),
                                            "__init__.py"))
        return None


class ModuleLoader(SourceFileLoader):

    def __init__(self, add_module, fullname, path):
        self.add_module = add_module
        SourceFileLoader.__init__(self, fullname, path)


    def _load(self, module, name):
        # Add the module to the global modules list
        self.add_module(module)
        logger.info("Module '%s' successfully imported from %s.", name.split(".", 2)[2], self.path)
        return module


    # Python 3.4
    def exec_module(self, module):
        super().exec_module(module)
        self._load(module, module.__spec__.name)


    # Python 3.3
    def load_module(self, fullname):
        module = super().load_module(fullname)
        return self._load(module, module.__name__)
