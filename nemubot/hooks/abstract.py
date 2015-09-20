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

def call_game(call, *args, **kargs):
    """With given args, try to determine the right call to make

    Arguments:
    call -- the function to call
    *args -- unamed arguments to pass, dictionnaries contains are placed into kargs
    **kargs -- named arguments
    """

    assert callable(call)

    l = list()
    d = kargs

    for a in args:
        if a is not None:
            if isinstance(a, dict):
                d.update(a)
            else:
                l.append(a)

    return call(*l, **d)


class Abstract:

    """Abstract class for Hook implementation"""

    def __init__(self, call, data=None, mtimes=-1, end_call=None):
        self.call = call
        self.data = data

        self.times = mtimes
        self.end_call = end_call


    def match(self, data1, server):
        return NotImplemented


    def run(self, data1, *args):
        """Run the hook"""

        from nemubot.exception import IRCException
        self.times -= 1

        try:
            ret = call_game(self.call, data1, self.data, *args)
        except IRCException as e:
            ret = e.fill_response(data1)
        finally:
            if self.times == 0:
                self.call_end(ret)

        return ret
