import unittest

import nemubot.server.IRC as IRC


class TestIRCMessage(unittest.TestCase):


    def setUp(self):
        self.msg = IRC.IRCMessage(b":toto!titi@RZ-3je16g.re PRIVMSG #the-channel :Can you parse this message?")


    def test_parsing(self):
        self.assertEqual(self.msg.prefix, "toto!titi@RZ-3je16g.re")
        self.assertEqual(self.msg.nick, "toto")
        self.assertEqual(self.msg.user, "titi")
        self.assertEqual(self.msg.host, "RZ-3je16g.re")

        self.assertEqual(len(self.msg.params), 2)

        self.assertEqual(self.msg.params[0], b"#the-channel")
        self.assertEqual(self.msg.params[1], b"Can you parse this message?")


    def test_prettyprint(self):
        bst1 = self.msg.to_server_string(False)
        msg2 = IRC.IRCMessage(bst1.encode())

        bst2 = msg2.to_server_string(False)
        msg3 = IRC.IRCMessage(bst2.encode())

        bst3 = msg3.to_server_string(False)

        self.assertEqual(bst2, bst3)


    def test_tags(self):
        self.assertEqual(len(self.msg.tags), 1)
        self.assertIn("time", self.msg.tags)

        self.msg.add_tag("time")
        self.assertEqual(len(self.msg.tags), 1)

        self.msg.add_tag("toto")
        self.assertEqual(len(self.msg.tags), 2)
        self.assertIn("toto", self.msg.tags)


if __name__ == '__main__':
    unittest.main()
