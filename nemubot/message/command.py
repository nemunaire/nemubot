# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2016  Mercier Pierre-Olivier
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

from nemubot.message.abstract import Abstract


class Command(Abstract):

    """This class represents a specialized TextMessage"""

    serializetag = "nemubotCommand"


    def __init__(self, cmd, args=None, kwargs=None, *nargs, **kargs):
        super().__init__(*nargs, **kargs)

        self.cmd = cmd
        self.args = args if args is not None else list()
        self.kwargs = kwargs if kwargs is not None else dict()


    def __repr__(self):
        return self.cmd + " @" + ",@".join(self.args)


    def addChild(self, name, child):
        if name == "list":
            self.args = child
        elif name == "dict":
            self.kwargs = child
        else:
            return False
        return True


    def serialize(self):
        from nemubot.datastore.nodes import ParsingNode
        node = ParsingNode(tag=Command.serializetag, cmd=self.cmd)
        if len(self.args):
            node.children.append(ParsingNode.serialize_node(self.args))
        if len(self.kwargs):
            node.children.append(ParsingNode.serialize_node(self.kwargs))
        return node


class OwnerCommand(Command):

    """This class represents a special command incomming from the owner"""

    serializetag = "nemubotOCommand"

    pass
