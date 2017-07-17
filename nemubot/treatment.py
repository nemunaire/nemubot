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
import types

logger = logging.getLogger("nemubot.treatment")


class MessageTreater:

    """Treat a message"""

    def __init__(self):
        from nemubot.hooks.manager import HooksManager
        self.hm = HooksManager()


    def treat_msg(self, msg):
        """Treat a given message

        Arguments:
        msg -- the message to treat
        """

        try:
            handled = False

            # Run pre-treatment: from Message to [ Message ]
            msg_gen = self._pre_treat(msg)
            m = next(msg_gen, None)

            # Run in-treatment: from Message to [ Response ]
            while m is not None:

                hook_gen = self._in_hooks(m)
                hook = next(hook_gen, None)
                if hook is not None:
                    handled = True

                    for response in self._in_treat(m, hook, hook_gen):
                        # Run post-treatment: from Response to [ Response ]
                        yield from self._post_treat(response)

                m = next(msg_gen, None)

            if not handled:
                for m in self._in_miss(msg):
                    yield from self._post_treat(m)
        except BaseException as e:
            logger.exception("Error occurred during the processing of the %s: "
                             "%s", type(msg).__name__, msg)

            from nemubot.message import Text
            yield from self._post_treat(Text("Sorry, an error occured (%s). Feel free to open a new issue at https://github.com/nemunaire/nemubot/issues/new" % type(e).__name__,
                                             to=msg.to_response))



    def _pre_treat(self, msg):
        """Modify input Messages

        Arguments:
        msg -- message to treat
        """

        for h in self.hm.get_hooks("pre", type(msg).__name__):
            if h.can_read(msg.to, msg.server) and h.match(msg):
                res = h.run(msg)

                if isinstance(res, list):
                    for i in range(len(res)):
                        # Avoid infinite loop
                        if res[i] != msg:
                            yield from self._pre_treat(res[i])

                elif res is not None and res != msg:
                    yield from self._pre_treat(res)

                elif res is None or res is False:
                    break
        else:
            yield msg


    def _in_hooks(self, msg):
        for h in self.hm.get_hooks("in", type(msg).__name__):
            if h.can_read(msg.to, msg.server) and h.match(msg):
                yield h


    def _in_treat(self, msg, hook, hook_gen):
        """Treats Messages and returns Responses

        Arguments:
        msg -- message to treat
        """

        if hasattr(msg, "frm_owner"):
            msg.frm_owner = (not hasattr(msg.server, "owner") or msg.server.owner == msg.frm)

        while hook is not None:
            res = hook.run(msg)

            if isinstance(res, list):
                for r in res:
                    yield r

            elif res is not None:
                if isinstance(res, types.GeneratorType):
                    for r in res:
                        if not hasattr(r, "server") or r.server is None:
                            r.server = msg.server

                        yield r

                else:
                    if not hasattr(res, "server") or res.server is None:
                        res.server = msg.server

                    yield res

            hook = next(hook_gen, None)


    def _in_miss(self, msg):
        from nemubot.message.command import Command as CommandMessage
        from nemubot.message.directask import DirectAsk as DirectAskMessage

        if isinstance(msg, CommandMessage):
            from nemubot.hooks import Command as CommandHook
            from nemubot.tools.human import guess
            hooks = self.hm.get_reverse_hooks("in", type(msg).__name__)
            suggest = [s for s in guess(msg.cmd, [h.name for h in hooks if isinstance(h, CommandHook) and h.name is not None])]
            if len(suggest) >= 1:
                yield DirectAskMessage(msg.frm,
                                       "Unknown command %s. Would you mean: %s?" % (msg.cmd, ", ".join(suggest)),
                                       to=msg.to_response)

        elif isinstance(msg, DirectAskMessage):
            yield DirectAskMessage(msg.frm,
                                   "Sorry, I'm just a bot and your sentence is too complex for me :( But feel free to teach me some tricks at https://github.com/nemunaire/nemubot/!",
                                   to=msg.to_response)


    def _post_treat(self, msg):
        """Modify output Messages

        Arguments:
        msg -- response to treat
        """

        for h in self.hm.get_hooks("post", type(msg).__name__):
            if h.can_write(msg.to, msg.server) and h.match(msg):
                res = h.run(msg)

                if isinstance(res, list):
                    for i in range(len(res)):
                        # Avoid infinite loop
                        if res[i] != msg:
                            yield from self._post_treat(res[i])

                elif res is not None and res != msg:
                    yield from self._post_treat(res)

                elif res is None or res is False:
                    break

        else:
            yield msg
