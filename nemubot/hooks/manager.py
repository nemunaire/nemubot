# -*- coding: utf-8 -*-

# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2014  nemunaire
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


class HooksManager:

    """Class to manage hooks"""

    def __init__(self):
        """Initialize the manager"""

        self.hooks = dict()


    def add_hook(self, hook, *triggers):
        """Add a hook to the manager

        Argument:
        hook -- a Hook instance
        triggers -- string that trigger the hook
        """

        trigger = "_".join(triggers)

        if trigger not in self.hooks:
            self.hooks[trigger] = list()

        #print("ADD hook: %s => %s" % (trigger, hook))
        self.hooks[trigger].append(hook)


    def del_hook(self, hook=None, *triggers):
        """Remove the given hook from the manager

        Return:
        Boolean value reporting the deletion success

        Argument:
        triggers -- trigger string to remove

        Keyword argument:
        hook -- a Hook instance to remove from the trigger string
        """

        trigger = "_".join(triggers)

        if trigger in self.hooks:
            if hook is None:
                del self.hooks[trigger]
            else:
                self.hooks[trigger].remove(hook)
            return True
        return False


    def get_hooks(self, *triggers):
        """Returns list of trigger hooks that match the given trigger string

        Argument:
        triggers -- the trigger string

        Keyword argument:
        data -- Data to pass to the hook as argument
        """

        trigger = "_".join(triggers)

        res = list()

        for key in self.hooks:
            if trigger.find(key) == 0:
                res += self.hooks[key]

        #print("GET hooks: %s => %d" % (trigger, len(res)))
        return res


    def exec_hook(self, *triggers, **data):
        """Trigger hooks that match the given trigger string

        Argument:
        trigger -- the trigger string

        Keyword argument:
        data -- Data to pass to the hook as argument
        """

        trigger = "_".join(triggers)

        for key in self.hooks:
            if trigger.find(key) == 0:
                for hook in self.hooks[key]:
                    hook.run(**data)
