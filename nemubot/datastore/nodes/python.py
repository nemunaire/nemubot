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

from nemubot.datastore.nodes.serializable import Serializable


class PythonTypeNode(Serializable):

    """XML node representing a Python simple type
    """

    def __init__(self, **kwargs):
        self.value = None
        self._cnt = ""


    def characters(self, content):
        self._cnt += content


    def endElement(self, name):
        raise NotImplemented


    def __repr__(self):
        return self.value.__repr__()


    def parsedForm(self):
        return self.value

    def serialize(self):
        raise NotImplemented


class IntNode(PythonTypeNode):

    serializetag = "int"

    def endElement(self, name):
        self.value = int(self._cnt)
        return True

    def serialize(self):
        from nemubot.datastore.nodes.generic import ParsingNode
        node = ParsingNode(tag=self.serializetag)
        node.content = str(self.value)
        return node


class FloatNode(PythonTypeNode):

    serializetag = "float"

    def endElement(self, name):
        self.value = float(self._cnt)
        return True

    def serialize(self):
        from nemubot.datastore.nodes.generic import ParsingNode
        node = ParsingNode(tag=self.serializetag)
        node.content = str(self.value)
        return node


class StringNode(PythonTypeNode):

    serializetag = "str"

    def endElement(self, name):
        self.value = str(self._cnt)
        return True

    def serialize(self):
        from nemubot.datastore.nodes.generic import ParsingNode
        node = ParsingNode(tag=self.serializetag)
        node.content = str(self.value)
        return node
