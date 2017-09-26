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

from nemubot.modulecontext import _ModuleContext

context = _ModuleContext()


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


def attach(pidfile, socketfile):
    import socket
    import sys

    # Read PID from pidfile
    with open(pidfile, "r") as f:
        pid = int(f.readline())

    print("nemubot is launched with PID %d. Attaching to Unix socket at: %s" % (pid, socketfile))

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(socketfile)
    except socket.error as e:
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        return 1

    import select
    mypoll = select.poll()

    mypoll.register(sys.stdin.fileno(), select.POLLIN | select.POLLPRI)
    mypoll.register(sock.fileno(), select.POLLIN | select.POLLPRI)
    try:
        while True:
            for fd, flag in mypoll.poll():
                if flag & (select.POLLERR | select.POLLHUP | select.POLLNVAL):
                    sock.close()
                    print("Connection closed.")
                    return 1

                if fd == sys.stdin.fileno():
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

                if fd == sock.fileno():
                    sys.stdout.write(sock.recv(2048).decode())

    except KeyboardInterrupt:
        pass
    except:
        return 1
    finally:
        sock.close()
    return 0


def daemonize(socketfile=None):
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
