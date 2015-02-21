# -*- coding: utf-8 -*-

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

import xml.sax

from nemubot.tools.xmlparser import node as module_state


class ModuleStatesFile(xml.sax.ContentHandler):

    def startDocument(self):
        self.root = None
        self.stack = list()

    def startElement(self, name, attrs):
        cur = module_state.ModuleState(name)

        for name in attrs.keys():
            cur.setAttribute(name, attrs.getValue(name))

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


def parse_file(filename):
    parser = xml.sax.make_parser()
    mod = ModuleStatesFile()
    parser.setContentHandler(mod)
    parser.parse(open(filename, "r"))
    return mod.root


def parse_string(string):
    mod = ModuleStatesFile()
    xml.sax.parseString(string, mod)
    return mod.root
