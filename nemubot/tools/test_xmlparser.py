import unittest

import io
import xml.parsers.expat

from nemubot.tools.xmlparser import XMLParser


class StringNode():
    def __init__(self):
        self.string = ""

    def characters(self, content):
        self.string += content

    def saveElement(self, store, tag="string"):
        store.startElement(tag, {})
        store.characters(self.string)
        store.endElement(tag)


class TestNode():
    def __init__(self, option=None):
        self.option = option
        self.mystr = None

    def addChild(self, name, child):
        self.mystr = child.string
        return True

    def saveElement(self, store, tag="test"):
        store.startElement(tag, {"option": self.option})

        strNode = StringNode()
        strNode.string = self.mystr
        strNode.saveElement(store)

        store.endElement(tag)


class Test2Node():
    def __init__(self, option=None):
        self.option = option
        self.mystrs = list()

    def startElement(self, name, attrs):
        if name == "string":
            self.mystrs.append(attrs["value"])
            return True

    def saveElement(self, store, tag="test"):
        store.startElement(tag, {"option": self.option} if self.option is not None else {})

        for mystr in self.mystrs:
            store.startElement("string", {"value": mystr})
            store.endElement("string")

        store.endElement(tag)


class TestXMLParser(unittest.TestCase):

    def test_parser1(self):
        p = xml.parsers.expat.ParserCreate()
        mod = XMLParser({"string": StringNode})

        p.StartElementHandler = mod.startElement
        p.CharacterDataHandler = mod.characters
        p.EndElementHandler = mod.endElement

        inputstr = "<string>toto</string>"
        p.Parse(inputstr, 1)

        self.assertEqual(mod.root.string, "toto")
        self.assertEqual(mod.saveDocument(header=False).getvalue(), inputstr)


    def test_parser2(self):
        p = xml.parsers.expat.ParserCreate()
        mod = XMLParser({"string": StringNode, "test": TestNode})

        p.StartElementHandler = mod.startElement
        p.CharacterDataHandler = mod.characters
        p.EndElementHandler = mod.endElement

        inputstr = '<test option="123"><string>toto</string></test>'
        p.Parse(inputstr, 1)

        self.assertEqual(mod.root.option, "123")
        self.assertEqual(mod.root.mystr, "toto")
        self.assertEqual(mod.saveDocument(header=False).getvalue(), inputstr)


    def test_parser3(self):
        p = xml.parsers.expat.ParserCreate()
        mod = XMLParser({"string": StringNode, "test": Test2Node})

        p.StartElementHandler = mod.startElement
        p.CharacterDataHandler = mod.characters
        p.EndElementHandler = mod.endElement

        inputstr = '<test><string value="toto"/><string value="toto2"/></test>'
        p.Parse(inputstr, 1)

        self.assertEqual(mod.root.option, None)
        self.assertEqual(len(mod.root.mystrs), 2)
        self.assertEqual(mod.root.mystrs[0], "toto")
        self.assertEqual(mod.root.mystrs[1], "toto2")
        self.assertEqual(mod.saveDocument(header=False, short_empty_elements=True).getvalue(), inputstr)


if __name__ == '__main__':
    unittest.main()
