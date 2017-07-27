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

class ListNode:

    """XML node representing a Python dictionnnary
    """

    def __init__(self, **kwargs):
        self.items = list()


    def addChild(self, name, child):
        self.items.append(child)
        return True


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


    def saveElement(self, store, tag="list"):
        store.startElement(tag, {})
        for i in self.items:
            i.saveElement(store)
        store.endElement(tag)


class DictNode:

    """XML node representing a Python dictionnnary
    """

    def __init__(self, **kwargs):
        self.items = dict()
        self._cur = None


    def startElement(self, name, attrs):
        if self._cur is None and "key" in attrs:
            self._cur = (attrs["key"], "")
            return True
        return False


    def characters(self, content):
        if self._cur is not None:
            key, cnt = self._cur
            if isinstance(cnt, str):
                cnt += content
                self._cur = key, cnt


    def endElement(self, name):
        if name is None or self._cur is None:
            return

        key, cnt = self._cur
        if isinstance(cnt, list) and len(cnt) == 1:
            self.items[key] = cnt
        else:
            self.items[key] = cnt

        self._cur = None
        return True


    def addChild(self, name, child):
        if self._cur is None:
            return False

        key, cnt = self._cur
        if not isinstance(cnt, list):
            cnt = []
        cnt.append(child)
        self._cur = key, cnt
        return True


    def __getitem__(self, item):
        return self.items[item]

    def __setitem__(self, item, v):
        self.items[item] = v

    def __contains__(self, item):
        return item in self.items

    def __repr__(self):
        return self.items.__repr__()


    def saveElement(self, store, tag="dict"):
        store.startElement(tag, {})
        for k, v in self.items.items():
            store.startElement("item", {"key": k})
            if isinstance(v, str):
                store.characters(v)
            else:
                for i in v:
                    i.saveElement(store)
            store.endElement("item")
        store.endElement(tag)
