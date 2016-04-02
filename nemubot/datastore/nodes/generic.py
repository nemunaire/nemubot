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


class ParsingNode:

    """Allow any kind of subtags, just keep parsed ones
    """

    def __init__(self, tag=None, **kwargs):
        self.tag = tag
        self.attrs = kwargs
        self.content = ""
        self.children = []


    def characters(self, content):
        self.content += content


    def addChild(self, name, child):
        self.children.append(child)
        return True


    def hasNode(self, nodename):
        return self.getNode(nodename) is not None


    def getNode(self, nodename):
        for c in self.children:
            if c is not None and c.tag == nodename:
                return c
        return None


    def __getitem__(self, item):
        return self.attrs[item]

    def __contains__(self, item):
        return item in self.attrs


    def serialize_node(node, **def_kwargs):
        """Serialize any node or basic data to a ParsingNode instance"""

        if isinstance(node, Serializable):
            node = node.serialize()

        if isinstance(node, str):
            from nemubot.datastore.nodes.python import StringNode
            pn = StringNode(**def_kwargs)
            pn.value = node
            return pn

        elif isinstance(node, int):
            from nemubot.datastore.nodes.python import IntNode
            pn = IntNode(**def_kwargs)
            pn.value = node
            return pn

        elif isinstance(node, float):
            from nemubot.datastore.nodes.python import FloatNode
            pn = FloatNode(**def_kwargs)
            pn.value = node
            return pn

        elif isinstance(node, list):
            from nemubot.datastore.nodes.basic import ListNode
            pn = ListNode(**def_kwargs)
            pn.items = node
            return pn.serialize()

        elif isinstance(node, dict):
            from nemubot.datastore.nodes.basic import DictNode
            pn = DictNode(**def_kwargs)
            pn.items = node
            return pn.serialize()

        else:
            assert isinstance(node, ParsingNode)
            return node


class GenericNode(ParsingNode):

    """Consider all subtags as dictionnary
    """

    def __init__(self, tag, **kwargs):
        super().__init__(tag, **kwargs)
        self._cur = None
        self._deep_cur = 0


    def startElement(self, name, attrs):
        if self._cur is None:
            self._cur = GenericNode(name, **attrs)
            self._deep_cur = 0
        else:
            self._deep_cur += 1
            self._cur.startElement(name, attrs)
        return True


    def characters(self, content):
        if self._cur is None:
            super().characters(content)
        else:
            self._cur.characters(content)


    def endElement(self, name):
        if name is None:
            return

        if self._deep_cur:
            self._deep_cur -= 1
            self._cur.endElement(name)
        else:
            self.children.append(self._cur)
            self._cur = None
        return True
