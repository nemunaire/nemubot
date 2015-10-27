import unittest

import xml.parsers.expat

from nemubot.tools.xmlparser import XMLParser


class StringNode():
    def __init__(self):
        self.string = ""

    def characters(self, content):
        self.string += content


class TestNode():
    def __init__(self, option=None):
        self.option = option
        self.mystr = None

    def addChild(self, name, child):
        self.mystr = child.string
        return True


class Test2Node():
    def __init__(self, option=None):
        self.option = option
        self.mystrs = list()

    def startElement(self, name, attrs):
        if name == "string":
            self.mystrs.append(attrs["value"])
            return True


class TestXMLParser(unittest.TestCase):

    def test_parser1(self):
        p = xml.parsers.expat.ParserCreate()
        mod = XMLParser({"string": StringNode})

        p.StartElementHandler = mod.startElement
        p.CharacterDataHandler = mod.characters
        p.EndElementHandler = mod.endElement

        p.Parse("<string>toto</string>", 1)

        self.assertEqual(mod.root.string, "toto")


    def test_parser2(self):
        p = xml.parsers.expat.ParserCreate()
        mod = XMLParser({"string": StringNode, "test": TestNode})

        p.StartElementHandler = mod.startElement
        p.CharacterDataHandler = mod.characters
        p.EndElementHandler = mod.endElement

        p.Parse("<test option='123'><string>toto</string></test>", 1)

        self.assertEqual(mod.root.option, "123")
        self.assertEqual(mod.root.mystr, "toto")


    def test_parser3(self):
        p = xml.parsers.expat.ParserCreate()
        mod = XMLParser({"string": StringNode, "test": Test2Node})

        p.StartElementHandler = mod.startElement
        p.CharacterDataHandler = mod.characters
        p.EndElementHandler = mod.endElement

        p.Parse("<test><string value='toto' /><string value='toto2' /></test>", 1)

        self.assertEqual(mod.root.option, None)
        self.assertEqual(len(mod.root.mystrs), 2)
        self.assertEqual(mod.root.mystrs[0], "toto")
        self.assertEqual(mod.root.mystrs[1], "toto2")


if __name__ == '__main__':
    unittest.main()
