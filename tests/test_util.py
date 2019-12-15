# vim: ts=4 sw=0 sts=-1 et ai tw=80

"""
Unit tests for util.py
"""

import unittest

import io

from autoperm.util import file_chars, strip_punc


class TestUtil(unittest.TestCase):
    def setUp(self):
        self.strings = [
                ("", ""),
                ("ABC", "ABC"),
                ("abc", "ABC"),
                ("aBc", "ABC"),
                (",A987B^&*C*", "ABC")]

    def test_file_chars(self):
        for input_text, _ in self.strings:
            self.assertEqual("".join(file_chars(io.StringIO(input_text))),
                             input_text)

    def test_strip_punc(self):
        for input_text, result in self.strings:
            self.assertEqual("".join(strip_punc(input_text)), result)


if __name__ == "__main__":
    unittest.main()
