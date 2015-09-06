import unittest

from nemubot.tools.human import size, word_distance

class TestHuman(unittest.TestCase):

    def test_size(self):
        self.assertEqual(size(42), "42 B")
        self.assertEqual(size(42, False), "42")
        self.assertEqual(size(1023), "1023 B")
        self.assertEqual(size(1024), "1 KiB")
        self.assertEqual(size(1024, False), "1")
        self.assertEqual(size(1025), "1.001 KiB")
        self.assertEqual(size(1025, False), "1.001")
        self.assertEqual(size(1024000), "1000 KiB")
        self.assertEqual(size(1024000, False), "1000")
        self.assertEqual(size(1024 * 1024), "1 MiB")
        self.assertEqual(size(1024 * 1024, False), "1")
        self.assertEqual(size(1024 * 1024 * 1024), "1 GiB")
        self.assertEqual(size(1024 * 1024 * 1024, False), "1")
        self.assertEqual(size(1024 * 1024 * 1024 * 1024), "1 TiB")
        self.assertEqual(size(1024 * 1024 * 1024 * 1024, False), "1")

    def test_Levenshtein(self):
        self.assertEqual(word_distance("", "a"), 1)
        self.assertEqual(word_distance("a", ""), 1)
        self.assertEqual(word_distance("a", "a"), 0)
        self.assertEqual(word_distance("a", "b"), 1)
        self.assertEqual(word_distance("aa", "ba"), 1)
        self.assertEqual(word_distance("ba", "ab"), 1)
        self.assertEqual(word_distance("long", "short"), 4)
        self.assertEqual(word_distance("long", "short"), word_distance("short", "long"))


if __name__ == '__main__':
    unittest.main()
