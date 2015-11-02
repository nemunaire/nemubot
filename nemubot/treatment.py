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
            # Run pre-treatment: from Message to [ Message ]
            msg_gen = self._pre_treat(msg)
            m = next(msg_gen, None)

            # Run in-treatment: from Message to [ Response ]
            while m is not None:
                for response in self._in_treat(m):
                    # Run post-treatment: from Response to [ Response ]
                    yield from self._post_treat(response)

                m = next(msg_gen, None)
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


    def _in_treat(self, msg):
        """Treats Messages and returns Responses

        Arguments:
        msg -- message to treat
        """

        for h in self.hm.get_hooks("in", type(msg).__name__):
            if h.can_read(msg.to, msg.server) and h.match(msg):
                res = h.run(msg)

                if isinstance(res, list):
                    for r in res:
                        yield r

                elif res is not None:
                    if not hasattr(res, "server") or res.server is None:
                        res.server = msg.server

                    yield res


    def _post_treat(self, msg):
        """Modify output Messages

        Arguments:
        msg -- response to treat
        """

        for h in self.hm.get_hooks("post"):
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
