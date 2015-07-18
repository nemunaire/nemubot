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

__version__ = '4.0.dev3'
__author__  = 'nemunaire'

from nemubot.modulecontext import ModuleContext

context = ModuleContext(None, None)


def requires_version(min=None, max=None):
    """Raise ImportError if the current version is not in the given range

    Keyword arguments:
    min -- minimal compatible version
    max -- last compatible version
    """

    from distutils.version import LooseVersion
    if min is not None and LooseVersion(__version__) < LooseVersion(str(min)):
        raise ImportError("Requires version above %s, "
                          "but this is nemubot v%s." % (str(min), __version__))
    if max is not None and LooseVersion(__version__) > LooseVersion(str(max)):
        raise ImportError("Requires version under %s, "
                          "but this is nemubot v%s." % (str(max), __version__))


def attach(pid, socketfile):
    import socket
    import sys

    print("nemubot is launched with PID %d. Attaching to Unix socket at: %s" % (pid, socketfile))

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(socketfile)
    except socket.error as e:
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        return 1

    from select import select
    try:
        while True:
            rl, wl, xl = select([sys.stdin, sock], [], [])

            if sys.stdin in rl:
                line = sys.stdin.readline().strip()
                if line == "exit" or line == "quit":
                    return 0
                elif line == "reload":
                    import os, signal
                    os.kill(pid, signal.SIGHUP)
                    print("Reload signal sent. Please wait...")

                elif line == "shutdown":
                    import os, signal
                    os.kill(pid, signal.SIGTERM)
                    print("Shutdown signal sent. Please wait...")

                elif line == "kill":
                    import os, signal
                    os.kill(pid, signal.SIGKILL)
                    print("Signal sent...")
                    return 0

                elif line == "stack" or line == "stacks":
                    import os, signal
                    os.kill(pid, signal.SIGUSR1)
                    print("Debug signal sent. Consult logs.")

                else:
                    sock.send(line.encode() + b'\r\n')

            if sock in rl:
                sys.stdout.write(sock.recv(2048).decode())
    except KeyboardInterrupt:
        pass
    except:
        return 1
    finally:
        sock.close()
    return 0


def daemonize():
    """Detach the running process to run as a daemon
    """

    import os
    import sys

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as err:
        sys.stderr.write("Unable to fork: %s\n" % err)
        sys.exit(1)

    os.setsid()
    os.umask(0)
    os.chdir('/')

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as err:
        sys.stderr.write("Unable to fork: %s\n" % err)
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.devnull, 'r')
    so = open(os.devnull, 'a+')
    se = open(os.devnull, 'a+')

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


def reload():
    """Reload code of all Python modules used by nemubot
    """

    import imp

    import nemubot.bot
    imp.reload(nemubot.bot)

    import nemubot.channel
    imp.reload(nemubot.channel)

    import nemubot.config
    imp.reload(nemubot.config)

    nemubot.config.reload()

    import nemubot.consumer
    imp.reload(nemubot.consumer)

    import nemubot.datastore
    imp.reload(nemubot.datastore)

    nemubot.datastore.reload()

    import nemubot.event
    imp.reload(nemubot.event)

    import nemubot.exception
    imp.reload(nemubot.exception)

    nemubot.exception.reload()

    import nemubot.hooks
    imp.reload(nemubot.hooks)

    nemubot.hooks.reload()

    import nemubot.importer
    imp.reload(nemubot.importer)

    import nemubot.message
    imp.reload(nemubot.message)

    nemubot.message.reload()

    import nemubot.server
    rl = nemubot.server._rlist
    wl = nemubot.server._wlist
    xl = nemubot.server._xlist
    imp.reload(nemubot.server)
    nemubot.server._rlist = rl
    nemubot.server._wlist = wl
    nemubot.server._xlist = xl

    nemubot.server.reload()

    import nemubot.tools
    imp.reload(nemubot.tools)

    nemubot.tools.reload()
