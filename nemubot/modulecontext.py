# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2017  Mercier Pierre-Olivier
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

class _ModuleContext:

    def __init__(self, module=None, knodes=None):
        self.module = module

        if module is not None:
            self.module_name = (module.__spec__.name if hasattr(module, "__spec__") else module.__name__).replace("nemubot.module.", "")
        else:
            self.module_name = ""

        self.hooks = list()
        self.events = list()
        self.debug = False

        from nemubot.config.module import Module
        self.config = Module(self.module_name)
        self._knodes = knodes


    def load_data(self):
        from nemubot.tools.xmlparser import module_state
        return module_state.ModuleState("nemubotstate")

    def set_knodes(self, knodes):
        self._knodes = knodes

    def set_default(self, default):
        # Access to data will trigger the load of data
        if self.data is None:
            self._data = default

    def add_hook(self, hook, *triggers):
        from nemubot.hooks import Abstract as AbstractHook
        assert isinstance(hook, AbstractHook), hook
        self.hooks.append((triggers, hook))

    def del_hook(self, hook, *triggers):
        from nemubot.hooks import Abstract as AbstractHook
        assert isinstance(hook, AbstractHook), hook
        self.hooks.remove((triggers, hook))

    def subtreat(self, msg):
        return None

    def add_event(self, evt, eid=None):
        return self.events.append((evt, eid))

    def del_event(self, evt):
        for i in self.events:
            e, eid = i
            if e == evt:
                self.events.remove(i)
                return True
        return False

    def send_response(self, server, res):
       self.module.logger.info("Send response: %s", res)

    def save(self):
        self.context.datastore.save(self.module_name, self.data)

    def subparse(self, orig, cnt):
        if orig.server in self.context.servers:
            return self.context.servers[orig.server].subparse(orig, cnt)

    @property
    def data(self):
        if not hasattr(self, "_data"):
            self._data = self.load_data()
        return self._data


    def unload(self):
        """Perform actions for unloading the module"""

        # Remove registered hooks
        for (s, h) in self.hooks:
            self.del_hook(h, *s)

        # Remove registered events
        for evt, eid in self.events:
            self.del_event(evt)

        self.save()


class ModuleContext(_ModuleContext):

    def __init__(self, context, *args, **kwargs):
        """Initialize the module context

        arguments:
        context -- the bot context
        module -- the module
        """

        super().__init__(*args, **kwargs)

        # Load module configuration if exists
        if self.module_name in context.modules_configuration:
            self.config = context.modules_configuration[self.module_name]

        self.context = context
        self.debug = context.debug


    def load_data(self):
        return self.context.datastore.load(self.module_name, self._knodes)

    def add_hook(self, hook, *triggers):
        from nemubot.hooks import Abstract as AbstractHook
        assert isinstance(hook, AbstractHook), hook
        self.hooks.append((triggers, hook))
        return self.context.treater.hm.add_hook(hook, *triggers)

    def del_hook(self, hook, *triggers):
        from nemubot.hooks import Abstract as AbstractHook
        assert isinstance(hook, AbstractHook), hook
        self.hooks.remove((triggers, hook))
        return self.context.treater.hm.del_hooks(*triggers, hook=hook)

    def subtreat(self, msg):
        yield from self.context.treater.treat_msg(msg)

    def add_event(self, evt, eid=None):
        return self.context.add_event(evt, eid, module_src=self.module)

    def del_event(self, evt):
        return self.context.del_event(evt, module_src=self.module)

    def send_response(self, server, res):
        if server in self.context.servers:
            if res.server is not None:
                return self.context.servers[res.server].send_response(res)
            else:
                return self.context.servers[server].send_response(res)
        else:
            self.module.logger.error("Try to send a message to the unknown server: %s", server)
            return False
