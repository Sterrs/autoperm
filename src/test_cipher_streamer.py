"""
Unit tests for CipherStreamer in autoperm.py
"""

import unittest

import io
import random

from cipher_streamer import CipherStreamer, chunk

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
        self.input_stripped = "SPHINXOFBLACKQUARTZJUDGEMYVOW\n"
        self.input_blocks_lines = "SPHIN XOFBL\nACKQU ARTZJ\nUDGEM YVOW\n"
        self.input_lines = "SPHINXOFBL\nACKQUARTZJ\nUDGEMYVOW\n"
        self.input_blocks = "SPHIN XOFBL ACKQU ARTZJ UDGEM YVOW\n"
        self.input_file = io.StringIO(self.input_text)
        self.output_file = io.StringIO()

    def test_chunk(self):
        self.assertEqual(list(chunk([], 1)), [])
        self.assertEqual(list(chunk([], 2)), [])
        self.assertEqual(list(chunk(range(4), 2)),
                         [(0, 1), (2, 3)])
        self.assertEqual(list(chunk(range(4), 3)),
                         [(0, 1, 2), (3, None, None)])
        self.assertEqual(list(chunk(range(4), 3, 4)),
                         [(0, 1, 2), (3, 4, 4)])

    def test_call(self):
        for g in self.generators:
            self.assertRaises(ValueError, CipherStreamer(g),
                              preserve=True, block=1)
            self.assertRaises(ValueError, CipherStreamer(g),
                              preserve=True, width=1)
            self.assertRaises(ValueError, CipherStreamer(g),
                              io.StringIO(), io.StringIO(), width=1, block=2)
            # shouldn't cause errors
            CipherStreamer(g)(io.StringIO(), io.StringIO(), block=0, width=1)
            CipherStreamer(g)(io.StringIO(), io.StringIO(), block=1, width=0)

    def test_preserve(self):
        for g in self.preservative_generators:
            self.setUp()
            CipherStreamer(g).preserve(self.input_file, self.output_file)
            self.assertEqual(self.input_text, self.output_file.getvalue())
        self.setUp()
        CipherStreamer(to_exes).preserve(self.input_file, self.output_file)
        self.assertEqual(self.output_file.getvalue(),
                         '"Xxxxxx (xx xxxxx xxxxxx), xxxxx xx xxx!?";')
        self.setUp()
        CipherStreamer(extra_exes).preserve(self.input_file, self.output_file)
        self.assertEqual(self.output_file.getvalue(),
                         ('"Xxxxxx (xx xxxxx xxxxxx), xxxxx xx xxx!?";'
                          'XXXXXXXXXXXXXXXXXXXXXXXXXXXXX'))
        self.setUp()
        CipherStreamer(not_enough_exes).preserve(self.input_file,
                                                 self.output_file)
        self.assertEqual(self.output_file.getvalue(),
                         '"Xxx (  ),   !?";')

    def test_strip(self):
        for g in self.preservative_generators:
            self.setUp()
            CipherStreamer(g).strip(self.input_file, self.output_file,
                                    block=0, width=0)
            self.assertEqual(self.input_stripped, self.output_file.getvalue())
            self.setUp()
            CipherStreamer(g).strip(self.input_file, self.output_file,
                                    block=5, width=0)
            self.assertEqual(self.input_blocks, self.output_file.getvalue())
            self.setUp()
            CipherStreamer(g).strip(self.input_file, self.output_file,
                                    block=0, width=10)
            self.assertEqual(self.input_lines, self.output_file.getvalue())
            for width in range(11, 17):
                self.setUp()
                CipherStreamer(g).strip(self.input_file, self.output_file,
                                        block=5, width=width)
                self.assertEqual(self.input_blocks_lines,
                                 self.output_file.getvalue())
            for width in 10, 17:
                self.setUp()
                CipherStreamer(g).strip(self.input_file, self.output_file,
                                        block=5, width=width)
                self.assertNotEqual(self.input_blocks_lines,
                                    self.output_file.getvalue())

if __name__ == "__main__":
    unittest.main()
