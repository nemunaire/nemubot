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
    import signal
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

    parser.add_argument("-P", "--pidfile", default="./nemubot.pid",
                        help="Path to the file where store PID")

    parser.add_argument("-S", "--socketfile", default="./nemubot.sock",
                        help="path where open the socket for internal communication")

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
    args.pidfile = os.path.abspath(os.path.expanduser(args.pidfile))
    args.socketfile = os.path.abspath(os.path.expanduser(args.socketfile))
    args.logfile = os.path.abspath(os.path.expanduser(args.logfile))
    args.files = [ x for x in map(os.path.abspath, args.files)]
    args.modules_path = [ x for x in map(os.path.abspath, args.modules_path)]

    # Check if an instance is already launched
    if args.pidfile is not None and os.path.isfile(args.pidfile):
        with open(args.pidfile, "r") as f:
            pid = int(f.readline())
        try:
            os.kill(pid, 0)
        except OSError:
            pass
        else:
            from nemubot import attach
            sys.exit(attach(pid))

    # Daemonize
    if not args.debug:
        from nemubot import daemonize
        daemonize()

    # Store PID to pidfile
    if args.pidfile is not None:
        with open(args.pidfile, "w+") as f:
            f.write(str(os.getpid()))

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
    module_finder = ModuleFinder(context.modules_paths, context.add_module)
    sys.meta_path.append(module_finder)

    # Load requested configuration files
    for path in args.files:
        if os.path.isfile(path):
            context.sync_queue.put_nowait(["loadconf", path])
        else:
            logger.error("%s is not a readable file", path)

    if args.module:
        for module in args.module:
            __import__(module)

    # Signals handling
    def sigtermhandler(signum, frame):
        """On SIGTERM and SIGINT, quit nicely"""
        context.quit()
    signal.signal(signal.SIGINT, sigtermhandler)
    signal.signal(signal.SIGTERM, sigtermhandler)

    def sighuphandler(signum, frame):
        """On SIGHUP, perform a deep reload"""
        import imp
        nonlocal nemubot, context, module_finder

        logger.debug("SIGHUP receive, iniate reload procedure...")

        # Reload nemubot Python modules
        imp.reload(nemubot)
        nemubot.reload()

        # Hotswap context
        import nemubot.bot
        context = nemubot.bot.hotswap(context)

        # Reload ModuleFinder
        sys.meta_path.remove(module_finder)
        module_finder = ModuleFinder(context.modules_paths, context.add_module)
        sys.meta_path.append(module_finder)

        # Reload configuration file
        for path in args.files:
            if os.path.isfile(path):
                context.sync_queue.put_nowait(["loadconf", path])
    signal.signal(signal.SIGHUP, sighuphandler)

    def sigusr1handler(signum, frame):
        """On SIGHUSR1, display stacktraces"""
        import traceback
        for threadId, stack in sys._current_frames().items():
            logger.debug("########### Thread %d:\n%s",
                         threadId,
                         "".join(traceback.format_stack(stack)))
    signal.signal(signal.SIGUSR1, sigusr1handler)

    if args.socketfile:
        from nemubot.server.socket import SocketListener
        context.add_server(SocketListener(context.add_server, "master_socket",
                                          sock_location=args.socketfile))

    # context can change when performing an hotswap, always join the latest context
    oldcontext = None
    while oldcontext != context:
        oldcontext = context
        context.start()
        context.join()

    # Wait for consumers
    logger.info("Waiting for other threads shuts down...")
    sys.exit(0)

if __name__ == "__main__":
    main()
