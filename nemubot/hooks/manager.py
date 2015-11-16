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

import logging


class HooksManager:

    """Class to manage hooks"""

    def __init__(self, name="core"):
        """Initialize the manager"""

        self.hooks = dict()
        self.logger = logging.getLogger("nemubot.hooks.manager." + name)


    def _access(self, *triggers):
        """Access to the given triggers chain"""

        h = self.hooks
        for t in triggers:
            if t not in h:
                h[t] = dict()
            h = h[t]

        if "__end__" not in h:
            h["__end__"] = list()

        return h


    def _search(self, hook, *where, start=None):
        """Search all occurence of the given hook"""

        if start is None:
            start = self.hooks

        for k in start:
            if k == "__end__":
                if hook in start[k]:
                    yield where
            else:
                yield from self._search(hook, *where + (k,), start=start[k])


    def add_hook(self, hook, *triggers):
        """Add a hook to the manager

        Argument:
        hook -- a Hook instance
        triggers -- string that trigger the hook
        """

        assert hook is not None, hook

        h = self._access(*triggers)

        h["__end__"].append(hook)

        self.logger.debug("New hook successfully added in %s: %s",
                           "/".join(triggers), hook)


    def del_hooks(self, *triggers, hook=None):
        """Remove the given hook from the manager

        Argument:
        triggers -- trigger string to remove

        Keyword argument:
        hook -- a Hook instance to remove from the trigger string
        """

        assert hook is not None or len(triggers)

        self.logger.debug("Trying to delete hook in %s: %s",
                           "/".join(triggers), hook)

        if hook is not None:
            for h in self._search(hook, *triggers, start=self._access(*triggers)):
                self._access(*h)["__end__"].remove(hook)

        else:
            if len(triggers):
                del self._access(*triggers[:-1])[triggers[-1]]
            else:
                self.hooks = dict()


    def get_hooks(self, *triggers):
        """Returns list of trigger hooks that match the given trigger string

        Argument:
        triggers -- the trigger string
        """

        for n in range(len(triggers) + 1):
            i = self._access(*triggers[:n])
            for h in i["__end__"]:
                yield h


    def get_reverse_hooks(self, *triggers, exclude_first=False):
        """Returns list of triggered hooks that are bellow or at the same level

        Argument:
        triggers -- the trigger string

        Keyword arguments:
        exclude_first -- start reporting hook at the next level
        """

        h = self._access(*triggers)
        for k in h:
            if k == "__end__":
                if not exclude_first:
                    for hk in h[k]:
                        yield hk
            else:
                yield from self.get_reverse_hooks(*triggers + (k,))
