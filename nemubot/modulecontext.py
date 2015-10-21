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

def convert_legacy_store(old):
    if old == "cmd_hook" or old == "cmd_rgxp" or old == "cmd_default":
        return "in_Command"
    elif old == "ask_hook" or old == "ask_rgxp" or old == "ask_default":
        return "in_DirectAsk"
    elif old == "msg_hook" or old == "msg_rgxp" or old == "msg_default":
        return "in_Text"
    elif old == "all_post":
        return "post"
    elif old == "all_pre":
        return "pre"
    else:
        return old


class ModuleContext:

    def __init__(self, context, module):
        """Initialize the module context

        arguments:
        context -- the bot context
        module -- the module
        """

        if module is not None:
            module_name = module.__spec__.name if hasattr(module, "__spec__") else module.__name__

        # Load module configuration if exists
        if (context is not None and
            module_name in context.modules_configuration):
            self.config = context.modules_configuration[module_name]
        else:
            from nemubot.tools.xmlparser.node import ModuleState
            self.config = ModuleState("module")

        self.hooks = list()
        self.events = list()
        self.debug = context.verbosity > 0 if context is not None else False

        # Define some callbacks
        if context is not None:
            # Load module data
            self.data = context.datastore.load(module_name)

            def add_hook(store, hook):
                store = convert_legacy_store(store)
                self.hooks.append((store, hook))
                return context.treater.hm.add_hook(hook, store)
            def del_hook(store, hook):
                store = convert_legacy_store(store)
                self.hooks.remove((store, hook))
                return context.treater.hm.del_hook(hook, store)
            def call_hook(store, msg):
                for h in context.treater.hm.get_hooks(store):
                    if h.match(msg):
                        res = h.run(msg)
                        if isinstance(res, list):
                            for i in res:
                                yield i
                        else:
                            yield res
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

            def add_hook(store, hook):
                store = convert_legacy_store(store)
                self.hooks.append((store, hook))
            def del_hook(store, hook):
                store = convert_legacy_store(store)
                self.hooks.remove((store, hook))
            def call_hook(store, msg):
                # TODO: what can we do here?
                return None
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
        self.call_hook = call_hook
        self.subtreat = subtreat


    def unload(self):
        """Perform actions for unloading the module"""

        # Remove registered hooks
        for (s, h) in self.hooks:
            self.del_hook(s, h)

        # Remove registered events
        for e in self.events:
            self.del_event(e)

        self.save()
