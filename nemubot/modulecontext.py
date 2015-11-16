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

class ModuleContext:

    def __init__(self, context, module):
        """Initialize the module context

        arguments:
        context -- the bot context
        module -- the module
        """

        if module is not None:
            module_name = module.__spec__.name if hasattr(module, "__spec__") else module.__name__
        else:
            module_name = ""

        # Load module configuration if exists
        if (context is not None and
            module_name in context.modules_configuration):
            self.config = context.modules_configuration[module_name]
        else:
            from nemubot.config.module import Module
            self.config = Module(module_name)

        self.hooks = list()
        self.events = list()
        self.debug = context.verbosity > 0 if context is not None else False

        from nemubot.hooks import Abstract as AbstractHook

        # Define some callbacks
        if context is not None:
            # Load module data
            self.data = context.datastore.load(module_name)

            def add_hook(hook, *triggers):
                assert isinstance(hook, AbstractHook), hook
                self.hooks.append((triggers, hook))
                return context.treater.hm.add_hook(hook, *triggers)

            def del_hook(hook, *triggers):
                assert isinstance(hook, AbstractHook), hook
                self.hooks.remove((triggers, hook))
                return context.treater.hm.del_hooks(*triggers, hook=hook)

            def subtreat(msg):
                yield from context.treater.treat_msg(msg)
            def add_event(evt, eid=None):
                return context.add_event(evt, eid, module_src=module)
            def del_event(evt):
                return context.del_event(evt, module_src=module)

            def send_response(server, res):
                if server in context.servers:
                    if res.server is not None:
                        return context.servers[res.server].send_response(res)
                    else:
                        return context.servers[server].send_response(res)
                else:
                    module.logger.error("Try to send a message to the unknown server: %s", server)
                    return False

        else:  # Used when using outside of nemubot
            from nemubot.tools.xmlparser import module_state
            self.data = module_state.ModuleState("nemubotstate")

            def add_hook(hook, *triggers):
                assert isinstance(hook, AbstractHook), hook
                self.hooks.append((triggers, hook))
            def del_hook(hook, *triggers):
                assert isinstance(hook, AbstractHook), hook
                self.hooks.remove((triggers, hook))
            def subtreat(msg):
                return None
            def add_event(evt, eid=None):
                return context.add_event(evt, eid, module_src=module)
            def del_event(evt):
                return context.del_event(evt, module_src=module)

            def send_response(server, res):
                module.logger.info("Send response: %s", res)

        def save():
            context.datastore.save(module_name, self.data)

        self.add_hook = add_hook
        self.del_hook = del_hook
        self.add_event = add_event
        self.del_event = del_event
        self.save = save
        self.send_response = send_response
        self.subtreat = subtreat


    def unload(self):
        """Perform actions for unloading the module"""

        # Remove registered hooks
        for (s, h) in self.hooks:
            self.del_hook(h, *s)

        # Remove registered events
        for e in self.events:
            self.del_event(e)

        self.save()
