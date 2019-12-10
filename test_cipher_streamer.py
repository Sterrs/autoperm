"""
Unit tests for CipherStreamer in autoperm.py
"""

import unittest

from autoperm import *

import io

# TODO: add some more tests here

# generators for use in TestCipherStreamer
def unchanged(text):
    for c in text:
        yield c

def to_upper(text):
    for c in text:
        yield c.upper()

def to_lower(text):
    for c in text:
        yield c.lower()

def to_random(text):
    for c in text:
        if random.random() < 0.5:
            yield c.lower()
        else:
            yield c.upper()

def to_exes(text):
    for c in text:
        yield "X"

def extra_exes(text):
    for c in text:
        yield "X"
        yield "X"

def not_enough_exes(text):
    yield from "XXX"

class TestCipherStreamer(unittest.TestCase):
    def setUp(self):
        self.preservative_generators = [
                unchanged, to_upper, to_lower, to_random]
        self.generators = [
                *self.preservative_generators,
                to_exes, extra_exes, not_enough_exes]
        self.input_text = '"Sphinx (of black quartz), judge my vow!?";'
        self.input_file = io.StringIO(self.input_text)
        self.output_file = io.StringIO()

    def test_cipher_streamer(self):
        for g in self.preservative_generators:
            self.setUp()
            CipherStreamer(g)(self.input_file, self.output_file)
            self.assertEqual(self.input_text, self.output_file.getvalue())

    def test_to_exes(self):
        CipherStreamer(to_exes)(self.input_file, self.output_file)
        self.assertEqual(self.output_file.getvalue(),
                         '"Xxxxxx (xx xxxxx xxxxxx), xxxxx xx xxx!?";')

    def test_extra_exes(self):
        CipherStreamer(extra_exes)(self.input_file, self.output_file)
        self.assertEqual(self.output_file.getvalue(),
                         ('"Xxxxxx (xx xxxxx xxxxxx), xxxxx xx xxx!?";'
                          'XXXXXXXXXXXXXXXXXXXXXXXXXXXXX'))

    def test_not_enough_exes(self):
        CipherStreamer(not_enough_exes)(self.input_file, self.output_file)
        self.assertEqual(self.output_file.getvalue(),
                         '"Xxx (  ),   !?";')

if __name__ == "__main__":
    unittest.main()
