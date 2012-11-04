#!/usr/bin/python3
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

import sys
import os
import imp
import traceback

import reloader
import prompt
import module_importer

VERSION = 3.1
module_importer.VERSION = VERSION
reloader.message.VERSION = VERSION

datas_path = "./datas/"
prompt.datas_path = datas_path
module_importer.datas_path = datas_path

servers = dict()

if __name__ == "__main__":
    #Add modules dir path
    if os.path.isdir("./modules/"):
        modules_path = os.path.realpath(os.path.abspath("./modules/"))
        if modules_path not in module_importer.modules_path:
            module_importer.modules_path.append(modules_path + "/")

    #Load given files
    if len(sys.argv) >= 2:
        for arg in sys.argv[1:]:
            if os.path.isfile(arg):
                prompt.load_file(arg, servers)
            elif os.path.isdir(arg):
                module_importer.modules_path.append(arg)

    print ("Nemubot ready, my PID is %i!" % (os.getpid()))
    while prompt.launch(servers):
        try:
            imp.reload(reloader)
            if module_importer.modules_loaded is None:
                reloader.reload()
                module_importer.modules_loaded = list()
            else:
                mods = module_importer.modules_loaded
                reloader.reload()
                module_importer.modules_loaded = mods
        except:
            print ("Unable to reload the prompt due to errors. Fix them before trying to reload the prompt.")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            sys.stdout.write (traceback.format_exception_only(exc_type, exc_value)[0])

    print ("Bye")
    sys.exit(0)
