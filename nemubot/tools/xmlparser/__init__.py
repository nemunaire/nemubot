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

import xml.parsers.expat

from nemubot.tools.xmlparser import node as module_state


class ModuleStatesFile:

    def __init__(self):
        self.root = None
        self.stack = list()

    def startElement(self, name, attrs):
        cur = module_state.ModuleState(name)

        for name in attrs.keys():
            cur.setAttribute(name, attrs[name])

        self.stack.append(cur)

    def characters(self, content):
        self.stack[len(self.stack)-1].content += content

    def endElement(self, name):
        child = self.stack.pop()
        size = len(self.stack)
        if size > 0:
            self.stack[size - 1].content = self.stack[size - 1].content.strip()
            self.stack[size - 1].addChild(child)
        else:
            self.root = child


class XMLParser:

    def __init__(self, knodes):
        self.knodes = knodes

        self.stack = list()
        self.child = 0


    def parse_file(self, path):
        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.startElement
        p.CharacterDataHandler = self.characters
        p.EndElementHandler = self.endElement

        with open(path, "rb") as f:
            p.ParseFile(f)

        return self.root


    def parse_string(self, s):
        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.startElement
        p.CharacterDataHandler = self.characters
        p.EndElementHandler = self.endElement

        p.Parse(s, 1)

        return self.root


    @property
    def root(self):
        if len(self.stack):
            return self.stack[0]
        else:
            return None


    @property
    def current(self):
        if len(self.stack):
            return self.stack[-1]
        else:
            return None


    def display_stack(self):
        return " in ".join([str(type(s).__name__) for s in reversed(self.stack)])


    def startElement(self, name, attrs):
        if not self.current or not hasattr(self.current, "startElement") or not self.current.startElement(name, attrs):
            if name not in self.knodes:
                raise TypeError(name + " is not a known type to decode")
            else:
                self.stack.append(self.knodes[name](**attrs))
        else:
            self.child += 1


    def characters(self, content):
        if self.current and hasattr(self.current, "characters"):
            self.current.characters(content)


    def endElement(self, name):
        if self.child:
            self.child -= 1

            if hasattr(self.current, "endElement"):
                self.current.endElement(name)
            return

        if hasattr(self.current, "endElement"):
            self.current.endElement(None)

        # Don't remove root
        if len(self.stack) > 1:
            last = self.stack.pop()
            if hasattr(self.current, "addChild"):
                if self.current.addChild(name, last):
                    return
            raise TypeError(name + " tag not expected in " + self.display_stack())

    def saveDocument(self, f=None, header=True, short_empty_elements=False):
        if f is None:
            import io
            f = io.StringIO()

        import xml.sax.saxutils
        gen = xml.sax.saxutils.XMLGenerator(f, "utf-8", short_empty_elements=short_empty_elements)
        if header:
            gen.startDocument()
        self.root.saveElement(gen)
        if header:
            gen.endDocument()

        return f


def parse_file(filename):
    p = xml.parsers.expat.ParserCreate()
    mod = ModuleStatesFile()

    p.StartElementHandler = mod.startElement
    p.EndElementHandler = mod.endElement
    p.CharacterDataHandler = mod.characters

    with open(filename, "rb") as f:
        p.ParseFile(f)

    return mod.root


def parse_string(string):
    p = xml.parsers.expat.ParserCreate()
    mod = ModuleStatesFile()

    p.StartElementHandler = mod.startElement
    p.EndElementHandler = mod.endElement
    p.CharacterDataHandler = mod.characters

    p.Parse(string, 1)

    return mod.root
