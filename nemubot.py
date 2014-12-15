#!/usr/bin/env python3.2
# -*- coding: utf-8 -*-

# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2014  Mercier Pierre-Olivier
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

import argparse
import imp
import logging
import os
import sys

import bot
import prompt
from prompt.builtins import load_file
import importer

if __name__ == "__main__":
    # Setup loggin interface
    logger = logging.getLogger("nemubot")

    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    fh = logging.FileHandler('./nemubot.log')
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    # Parse command line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument("-M", "--modules-path", nargs='*',
                        default=["./modules/"],
                        help="Directory to use as modules store")

    parser.add_argument("-D", "--data-path", default="./datas/",
                        help="Path to use to save bot data")

    parser.add_argument('files', metavar='FILE', nargs='*',
                        help="Configuration files to load")


    args = parser.parse_args()

    # Add modules dir paths
    modules_paths = list()
    for path in args.modules_path:
        if os.path.isdir(path):
            modules_paths.append(
                os.path.realpath(os.path.abspath(path)))
        else:
            logger.error("%s is not a directory", path)

    # Create bot context
    context = bot.Bot(modules_paths=modules_paths, data_path=args.data_path)

    # Load the prompt
    prmpt = prompt.Prompt()

    # Register the hook for futur import
    sys.meta_path.append(importer.ModuleFinder(context, prmpt))

    # Load requested configuration files
    for path in args.files:
        if os.path.isfile(path):
            load_file(path, context)
        else:
            logger.error("%s is not a readable file", path)

    print ("Nemubot v%s ready, my PID is %i!" % (bot.__version__,
                                                 os.getpid()))
    context.start()
    while prmpt.run(context):
        try:
            # Reload context
            imp.reload(bot)
            context = bot.hotswap(context)
            # Reload prompt
            imp.reload(prompt)
            prmpt = prompt.hotswap(prmpt)
            # Reload all other modules
            bot.reload()
            print("\033[1;32mContext reloaded\033[0m, now in Nemubot %s" %
                  bot.__version__)
            context.start()
        except:
            logger.exception("\033[1;31mUnable to reload the prompt due to "
                             "errors.\033[0m Fix them before trying to reload "
                             "the prompt.")

    context.quit()
    print("\nWaiting for other threads shuts down...")

    sys.exit(0)
