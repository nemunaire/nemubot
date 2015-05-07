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

def main():
    import os
    import sys

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--no-connect", action="store_true",
                        help="disable auto-connect to servers at startup")

    parser.add_argument("-v", "--verbose", action="count",
                        default=0,
                        help="verbosity level")

    parser.add_argument("-V", "--version", action="store_true",
                        help="display nemubot version and exit")

    parser.add_argument("-M", "--modules-path", nargs='*',
                        default=["./modules/"],
                        help="directory to use as modules store")

    parser.add_argument("-d", "--debug", action="store_true",
                        help="don't deamonize, keep in foreground")

    parser.add_argument("-l", "--logfile", default="./nemubot.log",
                        help="Path to store logs")

    parser.add_argument("-m", "--module", nargs='*',
                        help="load given modules")

    parser.add_argument("-D", "--data-path", default="./datas/",
                        help="path to use to save bot data")

    parser.add_argument('files', metavar='FILE', nargs='*',
                        help="configuration files to load")

    args = parser.parse_args()

    import nemubot

    if args.version:
        print(nemubot.__version__)
        sys.exit(0)

    # Resolve relatives paths
    args.data_path = os.path.abspath(os.path.expanduser(args.data_path))
    args.logfile = os.path.abspath(os.path.expanduser(args.logfile))
    args.files = [ x for x in map(os.path.abspath, args.files)]
    args.modules_path = [ x for x in map(os.path.abspath, args.modules_path)]

    # Daemonize
    if not args.debug:
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as err:
            sys.stderr.write("Unable to fork: %s" % err)
            sys.exit(1)

        os.setsid()
        os.umask(0)
        os.chdir('/')

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as err:
            sys.stderr.write("Unable to fork: %s" % err)
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    # Setup loggin interface
    import logging
    logger = logging.getLogger("nemubot")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s')

    if args.debug:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        if args.verbose < 2:
            ch.setLevel(logging.INFO)
        logger.addHandler(ch)

    fh = logging.FileHandler(args.logfile)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Add modules dir paths
    modules_paths = list()
    for path in args.modules_path:
        if os.path.isdir(path):
            modules_paths.append(path)
        else:
            logger.error("%s is not a directory", path)

    # Create bot context
    from nemubot import datastore
    from nemubot.bot import Bot
    context = Bot(modules_paths=modules_paths,
                  data_store=datastore.XML(args.data_path),
                  verbosity=args.verbose)

    if args.no_connect:
        context.noautoconnect = True

    # Load the prompt
    import nemubot.prompt
    prmpt = nemubot.prompt.Prompt()

    # Register the hook for futur import
    from nemubot.importer import ModuleFinder
    sys.meta_path.append(ModuleFinder(context.modules_paths, context.add_module))

    # Load requested configuration files
    for path in args.files:
        if os.path.isfile(path):
            context.sync_queue.put_nowait(["loadconf", path])
        else:
            logger.error("%s is not a readable file", path)

    if args.module:
        for module in args.module:
            __import__(module)

    context.start()
    context.join()

    logger.info("Waiting for other threads shuts down...")
    sys.exit(0)

if __name__ == "__main__":
    main()
