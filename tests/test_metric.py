# vim: ts=4 sw=0 sts=-1 et ai tw=80

"""
Unit tests for metric.py
"""

import unittest

import collections
import random
import string

from math import inf

from autoperm.util import strip_punc

from autoperm.metric import (
        BEE_MOVIE, blind_distribution, normalise, chi_squared, Metric, ioc,
        frequency_goodness_of_fit, blind_frequency_fit)

ALL_ONES_SENTINEL = object()
WANTS_ARGUMENTS_SENTINEL = object()


@Metric
def all_ones(text):
    return ALL_ONES_SENTINEL


@Metric
def counts_input_size(text):
    return sum(1 for _ in text)


@Metric
def wants_arguments(text, arg1, arg2, *, arg3):
    return WANTS_ARGUMENTS_SENTINEL


class TestMetric(unittest.TestCase):
    def test_blind_distribution(self):
        self.assertEqual(blind_distribution({}), {})
        self.assertEqual(blind_distribution({1: 1}), {0: 1})
        self.assertEqual(blind_distribution({1: 0.2, 2: 0.3}), {0: 0.3, 1: 0.2})
        for i in range(20):
            test_data = list(range(i))
            random.shuffle(test_data)
            test_dist = blind_distribution(dict(zip(range(i), test_data)))
            self.assertTrue(all(test_dist[j] == i + ~j for j in range(i)))

    # these should be stable-ish as everything is a dyadic rational which can be
    # represented exactly as a float. But I'm still kind of at the mercy of IEEE
    # 754 / the Python people
    def test_normalise(self):
        self.assertEqual(normalise({1: 3}), {1: 1.0})
        self.assertEqual(normalise({1: 9, 2: 9}), {1: 0.5, 2: 0.5})
        self.assertEqual(normalise({1: 3, 2: 9}), {1: 0.25, 2: 0.75})
        self.assertEqual(normalise({1: 3, 2: 6, 3: 3}),
                                   {1: 0.25, 2: 0.5, 3: 0.25})
        self.assertAlmostEqual(
                sum(normalise(
                        collections.Counter(strip_punc(BEE_MOVIE))).values()),
                1)

    def test_chi_squared(self):
        self.assertEqual(chi_squared({1: 0.2, 2: 0.8}, {1: 0.2, 2: 0.8}), 0)
        # exercise for the reader: prove this pattern holds in general
        # all of these are testing for exact equality, because I expect the
        # results to be nice-looking numbers, and I'd like to be informed about
        # it if any changes introduce enough numerical instability to break
        # this.
        self.assertEqual(chi_squared({1: 1}, {1: 1}), 0)
        self.assertEqual(chi_squared({1: 1}, {1: 0.5, 2: 0.5}), 1)
        self.assertEqual(chi_squared({1: 1}, {i: 0.25 for i in range(4)}), 3)
        self.assertEqual(chi_squared({1: 1}, {i: 0.125 for i in range(8)}), 7)
        self.assertEqual(chi_squared({1: 0.5, 2: 0.5},
                                     {i: 0.125 for i in range(8)}),
                         3)
        self.assertEqual(chi_squared({i: 0.25 for i in range(4)},
                                     {i: 0.125 for i in range(8)}),
                         1)
        self.assertEqual(chi_squared({1: 1}, {1: 0, 2: 1}), inf)
        self.assertEqual(chi_squared({1: 1}, {2: 1}), inf)
        self.assertEqual(chi_squared({1: 0, 2: 1}, {1: 0, 2: 1}), 0)
        self.assertEqual(chi_squared({1: 0, 2: 1}, {2: 1}), 0)
        for i in range(2, 20):
            test_dist = normalise({j: random.random() for j in range(i)})
            self.assertEqual(chi_squared(test_dist, test_dist), 0)
            elem, = random.sample(list(test_dist), 1)
            new_dist = test_dist.copy()
            new_dist[elem] += 1
            new_dist = normalise(new_dist)
            self.assertGreater(chi_squared(new_dist, test_dist), 0)

    def test_metric_call(self):
        self.assertIs(all_ones(""), ALL_ONES_SENTINEL)
        self.assertIs(all_ones("ABC"), ALL_ONES_SENTINEL)
        self.assertEqual(counts_input_size("ABC"), 3)
        self.assertEqual(counts_input_size("ABC<^*&("), 3)
        self.assertIs(wants_arguments("ABC", 1, 2, arg3=2),
                      WANTS_ARGUMENTS_SENTINEL)
        self.assertIs(wants_arguments("ABC", 1, arg2=2, arg3=2),
                      WANTS_ARGUMENTS_SENTINEL)
        self.assertIs(all_ones(BEE_MOVIE), ALL_ONES_SENTINEL)
        self.assertRaises(TypeError, all_ones)
        self.assertRaises(TypeError, all_ones, xyz=1)
        self.assertRaises(TypeError, wants_arguments, "ABC")
        self.assertRaises(TypeError, wants_arguments, "ABC", 1, 2)
        self.assertRaises(TypeError, wants_arguments, "ABC", 1, arg3=3)
        self.assertRaises(TypeError, wants_arguments, "ABC", arg2=2, arg3=3)

    def test_metric_no_strip(self):
        self.assertEqual(counts_input_size.no_strip("ABC<^*&("), 8)
        self.assertEqual(counts_input_size.no_strip(""), 0)
        self.assertEqual(counts_input_size.no_strip(" "), 1)
        self.assertEqual(counts_input_size.no_strip("%^&"), 3)

    def test_metric_random(self):
        self.assertIs(all_ones.random(), ALL_ONES_SENTINEL)
        self.assertEqual(counts_input_size.random(123), 123)
        self.assertEqual(counts_input_size.random(0), 0)
        self.assertEqual(counts_input_size.random(1), 1)

    def test_metric_english(self):
        all_ones.english()
        counts_input_size.english()

    def test_ioc(self):
        # see test_chi_squared for why this is Equal rather than AlmostEqual
        self.assertEqual(ioc(""), 0)
        self.assertEqual(ioc("a"), 0)
        self.assertEqual(ioc("ab"), 0)
        self.assertEqual(ioc("aa"), 26)
        self.assertEqual(ioc(string.ascii_uppercase), 0)
        self.assertAlmostEqual(ioc(string.ascii_uppercase * 2), 26 / 51)
        self.assertAlmostEqual(ioc(string.ascii_uppercase * 3), 2 * 26 / 77)
        test_letters = random.choices(string.ascii_uppercase, k=100)
        test_ioc_val = ioc(test_letters)
        for _ in range(100):
            random.shuffle(test_letters)
            self.assertAlmostEqual(test_ioc_val, ioc(test_letters))
        self.assertAlmostEqual(ioc(string.ascii_uppercase * 1000), 1, 2)
        # this is calculated by the program itself, so is not so much to ensure
        # correctness as it is to ensure that future versions agree with this
        # version
        self.assertAlmostEqual(ioc(BEE_MOVIE), 1.6580633101954148)
        self.assertAlmostEqual(ioc("Sphinx of black quartz, judge my vow"),
                               0.1921182266009852)

    def test_frequency_goodness_of_fit(self):
        # degenerates into sum(e for e in expected_dist), so should be 1
        self.assertAlmostEqual(blind_frequency_fit(""), 1)
        self.assertAlmostEqual(blind_frequency_fit("??^^*& "), 1)
        self.assertAlmostEqual(frequency_goodness_of_fit(BEE_MOVIE),
                               0.03262926444774889)
        self.assertAlmostEqual(
                frequency_goodness_of_fit(string.ascii_uppercase),
                5.609745671691266)
        self.assertAlmostEqual(
                frequency_goodness_of_fit(
                    "Sphinx of black quartz, judge my vow"),
                4.534500972024841)

    def test_blind_frequency_fit(self):
        self.assertAlmostEqual(blind_frequency_fit(""), 1)
        self.assertAlmostEqual(blind_frequency_fit("??^^*& "), 1)
        self.assertAlmostEqual(blind_frequency_fit(BEE_MOVIE),
                               0.008873441200834949)
        self.assertAlmostEqual(
                blind_frequency_fit(string.ascii_uppercase),
                5.609745671691266)
        self.assertAlmostEqual(
                blind_frequency_fit(
                    "Sphinx of black quartz, judge my vow"),
                4.423343098394534)


if __name__ == "__main__":
    unittest.main()
