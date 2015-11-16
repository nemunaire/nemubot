#!/usr/bin/env python3

import unittest

from nemubot.hooks.manager import HooksManager

class TestHookManager(unittest.TestCase):


    def test_access(self):
        hm = HooksManager()

        h1 = "HOOK1"
        h2 = "HOOK2"
        h3 = "HOOK3"

        hm.add_hook(h1)
        hm.add_hook(h2, "pre")
        hm.add_hook(h3, "pre", "Text")
        hm.add_hook(h2, "post", "Text")

        self.assertIn("__end__", hm._access())
        self.assertIn("__end__", hm._access("pre"))
        self.assertIn("__end__", hm._access("pre", "Text"))
        self.assertIn("__end__", hm._access("post", "Text"))

        self.assertFalse(hm._access("inexistant")["__end__"])
        self.assertTrue(hm._access()["__end__"])
        self.assertTrue(hm._access("pre")["__end__"])
        self.assertTrue(hm._access("pre", "Text")["__end__"])
        self.assertTrue(hm._access("post", "Text")["__end__"])


    def test_search(self):
        hm = HooksManager()

        h1 = "HOOK1"
        h2 = "HOOK2"
        h3 = "HOOK3"
        h4 = "HOOK4"

        hm.add_hook(h1)
        hm.add_hook(h2, "pre")
        hm.add_hook(h3, "pre", "Text")
        hm.add_hook(h2, "post", "Text")

        self.assertTrue([h for h in hm._search(h1)])
        self.assertFalse([h for h in hm._search(h4)])
        self.assertEqual(2, len([h for h in hm._search(h2)]))
        self.assertEqual([("pre", "Text")], [h for h in hm._search(h3)])


    def test_delete(self):
        hm = HooksManager()

        h1 = "HOOK1"
        h2 = "HOOK2"
        h3 = "HOOK3"
        h4 = "HOOK4"

        hm.add_hook(h1)
        hm.add_hook(h2, "pre")
        hm.add_hook(h3, "pre", "Text")
        hm.add_hook(h2, "post", "Text")

        hm.del_hooks(hook=h4)

        self.assertTrue(hm._access("pre")["__end__"])
        self.assertTrue(hm._access("pre", "Text")["__end__"])
        hm.del_hooks("pre")
        self.assertFalse(hm._access("pre")["__end__"])

        self.assertTrue(hm._access("post", "Text")["__end__"])
        hm.del_hooks("post", "Text", hook=h2)
        self.assertFalse(hm._access("post", "Text")["__end__"])

        self.assertTrue(hm._access()["__end__"])
        hm.del_hooks(hook=h1)
        self.assertFalse(hm._access()["__end__"])


    def test_get(self):
        hm = HooksManager()

        h1 = "HOOK1"
        h2 = "HOOK2"
        h3 = "HOOK3"

        hm.add_hook(h1)
        hm.add_hook(h2, "pre")
        hm.add_hook(h3, "pre", "Text")
        hm.add_hook(h2, "post", "Text")

        self.assertEqual([h1, h2], [h for h in hm.get_hooks("pre")])
        self.assertEqual([h1, h2, h3], [h for h in hm.get_hooks("pre", "Text")])


    def test_get_rev(self):
        hm = HooksManager()

        h1 = "HOOK1"
        h2 = "HOOK2"
        h3 = "HOOK3"

        hm.add_hook(h1)
        hm.add_hook(h2, "pre")
        hm.add_hook(h3, "pre", "Text")
        hm.add_hook(h2, "post", "Text")

        self.assertEqual([h2, h3], [h for h in hm.get_reverse_hooks("pre")])
        self.assertEqual([h3], [h for h in hm.get_reverse_hooks("pre", exclude_first=True)])


if __name__ == '__main__':
    unittest.main()
