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


class ListNode(Serializable):

    """XML node representing a Python dictionnnary
    """

    serializetag = "list"

    def __init__(self, **kwargs):
        self.items = list()


    def addChild(self, name, child):
        self.items.append(child)
        return True

    def parsedForm(self):
        return self.items


    def __len__(self):
        return len(self.items)

    def __getitem__(self, item):
        return self.items[item]

    def __setitem__(self, item, v):
        self.items[item] = v

    def __contains__(self, item):
        return item in self.items

    def __repr__(self):
        return self.items.__repr__()


    def serialize(self):
        from nemubot.datastore.nodes.generic import ParsingNode
        node = ParsingNode(tag=self.serializetag)
        for i in self.items:
            node.children.append(ParsingNode.serialize_node(i))
        return node


class DictNode(Serializable):

    """XML node representing a Python dictionnnary
    """

    serializetag = "dict"

    def __init__(self, **kwargs):
        self.items = dict()
        self._cur = None


    def startElement(self, name, attrs):
        if self._cur is None and "key" in attrs:
            self._cur = attrs["key"]
        return False

    def addChild(self, name, child):
        if self._cur is None:
            return False

        self.items[self._cur] = child
        self._cur = None
        return True

    def parsedForm(self):
        return self.items


    def __getitem__(self, item):
        return self.items[item]

    def __setitem__(self, item, v):
        self.items[item] = v

    def __contains__(self, item):
        return item in self.items

    def __repr__(self):
        return self.items.__repr__()


    def serialize(self):
        from nemubot.datastore.nodes.generic import ParsingNode
        node = ParsingNode(tag=self.serializetag)
        for k in self.items:
            chld = ParsingNode.serialize_node(self.items[k])
            chld.attrs["key"] = k
            node.children.append(chld)
        return node
