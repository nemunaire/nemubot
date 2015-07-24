import unittest

from nemubot.tools.human import size, word_distance

class TestHuman(unittest.TestCase):

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
