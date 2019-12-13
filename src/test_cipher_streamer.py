"""
Unit tests for CipherStreamer in autoperm.py
"""

import unittest

import io
import random
import textwrap as tw

from cipher_streamer import CipherStreamer, chunk, get_lines

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
        self.input_stripped_compare = tw.dedent("""\
                i:SPHINXOFBLACKQUARTZJUDGEMYVOW
                o:XXXXXXXXXXXXXXXXXXXXXXXXXXXXX

                """)
        self.input_stripped_compare_short = tw.dedent("""\
                i:SPHINXOFBLACKQUARTZJUDGEMYVOW
                o:XXX

                """)
        self.input_stripped_compare_extra = tw.dedent("""\
                i:SPHINXOFBLACKQUARTZJUDGEMYVOW
                o:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

                """)
        self.input_blocks_lines = tw.dedent("""\
                SPHIN XOFBL
                ACKQU ARTZJ
                UDGEM YVOW
                """)
        self.input_blocks_lines_compare = tw.dedent("""\
                i:SPHIN XOFBL
                o:XXXXX XXXXX

                i:ACKQU ARTZJ
                o:XXXXX XXXXX

                i:UDGEM YVOW
                o:XXXXX XXXX

                """)
        self.input_blocks_lines_compare_short = tw.dedent("""\
                i:SPHIN XOFBL
                o:XXX

                i:ACKQU ARTZJ
                o:

                i:UDGEM YVOW
                o:

                """)
        self.input_blocks_lines_compare_extra = tw.dedent("""\
                i:SPHIN XOFBL
                o:XXXXX XXXXX

                i:ACKQU ARTZJ
                o:XXXXX XXXXX

                i:UDGEM YVOW
                o:XXXXX XXXXX

                i:
                o:XXXXX XXXXX

                i:
                o:XXXXX XXXXX

                i:
                o:XXXXX XXX

                """)
        self.input_lines = tw.dedent("""\
                SPHINXOFBL
                ACKQUARTZJ
                UDGEMYVOW
                """)
        self.input_lines_compare = tw.dedent("""\
                i:SPHINXOFBL
                o:XXXXXXXXXX

                i:ACKQUARTZJ
                o:XXXXXXXXXX

                i:UDGEMYVOW
                o:XXXXXXXXX

                """)
        self.input_lines_compare_short = tw.dedent("""\
                i:SPHINXOFBL
                o:XXX

                i:ACKQUARTZJ
                o:

                i:UDGEMYVOW
                o:

                """)
        self.input_lines_compare_extra = tw.dedent("""\
                i:SPHINXOFBL
                o:XXXXXXXXXX

                i:ACKQUARTZJ
                o:XXXXXXXXXX

                i:UDGEMYVOW
                o:XXXXXXXXXX

                i:
                o:XXXXXXXXXX

                i:
                o:XXXXXXXXXX

                i:
                o:XXXXXXXX

                """)
        self.input_blocks = "SPHIN XOFBL ACKQU ARTZJ UDGEM YVOW\n"
        self.input_blocks_compare = tw.dedent("""\
                i:SPHIN XOFBL ACKQU ARTZJ UDGEM YVOW
                o:XXXXX XXXXX XXXXX XXXXX XXXXX XXXX

                """)
        self.input_blocks_compare_short = tw.dedent("""\
                i:SPHIN XOFBL ACKQU ARTZJ UDGEM YVOW
                o:XXX

                """)
        self.input_blocks_compare_extra = tw.dedent("""\
                i:SPHIN XOFBL ACKQU ARTZJ UDGEM YVOW
                o:XXXXX XXXXX XXXXX XXXXX XXXXX XXXXX

                i:
                o:XXXXX XXXXX XXXXX XXXXX XXXXX XXX

                """)
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
            self.assertRaises(TypeError, CipherStreamer(g))
            self.assertRaises(TypeError, CipherStreamer(g), "xyz", 1)
            self.assertRaises(TypeError, CipherStreamer(g), a=123)

    def test_preserve(self):
        for g in self.preservative_generators:
            self.setUp()
            CipherStreamer(g).preserve(self.input_file, self.output_file)
            self.assertEqual(self.input_text, self.output_file.getvalue())
            self.setUp()
            CipherStreamer(g).preserve(io.StringIO(), self.output_file)
            self.assertEqual("", self.output_file.getvalue())
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

    # currently this is basically a rip-off of test_strip
    def test_get_lines(self):
        # these two should always return one line
        self.assertEqual(list(get_lines("", block=0, width=0)), [""])
        self.assertEqual(list(get_lines("", block=1, width=0)), [""])
        self.assertEqual(list(get_lines("", block=0, width=1)), [])
        self.assertEqual(list(get_lines("", block=1, width=1)), [])
        self.assertEqual(list(get_lines(self.input_stripped.strip(),
                                        block=0, width=0)),
                         self.input_stripped.strip().split("\n"))
        self.assertEqual(list(get_lines(self.input_stripped.strip(),
                                        block=5, width=0)),
                         self.input_blocks.strip().split("\n"))
        self.assertEqual(list(get_lines(self.input_stripped.strip(),
                                        block=0, width=10)),
                         self.input_lines.strip().split("\n"))
        for width in range(11, 17):
            self.assertEqual(
                    list(get_lines(self.input_stripped.strip(),
                                   block=5, width=width)),
                    self.input_blocks_lines.strip().split("\n"))
        for width in 10, 17:
            self.assertNotEqual(
                    list(get_lines(self.input_stripped.strip(),
                                   block=5, width=width)),
                    self.input_blocks_lines.strip().split("\n"))

    def test_strip(self):
        # Also test the lowercase version in each case, with a nice D.R.Y loop
        for lowercase, case_func in ((True, str.lower), (False, lambda s: s)):
            for g in self.preservative_generators:
                self.setUp()
                CipherStreamer(g).strip(self.input_file, self.output_file,
                                        block=0, width=0, lowercase=lowercase)
                self.assertEqual(case_func(self.input_stripped),
                                 self.output_file.getvalue())
                self.setUp()
                CipherStreamer(g).strip(self.input_file, self.output_file,
                                        block=5, width=0, lowercase=lowercase)
                self.assertEqual(case_func(self.input_blocks),
                                 self.output_file.getvalue())
                self.setUp()
                CipherStreamer(g).strip(self.input_file, self.output_file,
                                        block=0, width=10, lowercase=lowercase)
                self.assertEqual(case_func(self.input_lines),
                                 self.output_file.getvalue())
                for width in range(11, 17):
                    self.setUp()
                    CipherStreamer(g).strip(self.input_file, self.output_file,
                                            block=5, width=width,
                                            lowercase=lowercase)
                    self.assertEqual(case_func(self.input_blocks_lines),
                                     self.output_file.getvalue())
                for width in 10, 17:
                    self.setUp()
                    CipherStreamer(g).strip(self.input_file, self.output_file,
                                            block=5, width=width,
                                            lowercase=lowercase)
                    self.assertNotEqual(case_func(self.input_blocks_lines),
                                        self.output_file.getvalue())
            # a bit of meta-hackery here to make things more concise. I think
            # it's forgiveable if it's in testing code anyway
            for g, postfix in ((to_exes, ""),
                               (not_enough_exes, "_short"),
                               (extra_exes, "_extra")):
                self.setUp()
                CipherStreamer(g).strip(self.input_file, self.output_file,
                                        block=0, width=0, compare=True,
                                        lowercase=lowercase)
                self.assertEqual(
                        case_func(vars(self)[
                            "input_stripped_compare{}".format(postfix)]),
                        self.output_file.getvalue())

if __name__ == "__main__":
    unittest.main()
