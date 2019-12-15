# vim: ts=4 sw=0 sts=-1 et ai tw=80

"""
Computing metrics on text
"""

import random
import string
import collections

from math import inf
from pathlib import Path

from util import strip_punc

# avoids problems where CWD is not the directory the source file is in
BEE_MOVIE_PATH = Path(__file__).parent / ".." / "texts" / "beemovie.txt"
with BEE_MOVIE_PATH.open("r") as f:
    BEE_MOVIE = f.read()


def blind_distribution(dist):
    """
    Convert a distribution into a "blind" distribution, indexed by 0, 1, 2, ...
    which is sorted in decreasing order (so the most frequent element is item
    0). Decreasing order is important so that the most frequent elements line
    up, rather than the least frequent.
    """
    return dict(enumerate(sorted(dist.values(), reverse=True)))


def normalise(dist):
    """
    Normalise some distribution, represented as a mapping
    """
    total = sum(dist.values())
    return {k: v / total for k, v in dist.items()}


# re-normalise it, to make the total expected frequency be much closer to 1.
# This kind of dubiously modifies the frequencies (although they stay in the
# same ratios), but really it is kind of necessary to make later statistical
# tests be well-defined.
# TODO: instead fix this by just finding (or generating) a canonical data-set
#       with many significant figures
ENGLISH_FREQUENCIES = normalise(
        {'A': 0.08167, 'B': 0.01492, 'C': 0.02202, 'D': 0.04253, 'E': 0.12702,
         'F': 0.02228, 'G': 0.02015, 'H': 0.06094, 'I': 0.06966, 'J': 0.00153,
         'K': 0.01292, 'L': 0.04025, 'M': 0.02406, 'N': 0.06749, 'O': 0.07507,
         'P': 0.01929, 'Q': 0.00095, 'R': 0.05987, 'S': 0.06327, 'T': 0.09356,
         'U': 0.02758, 'V': 0.00978, 'W': 0.02560, 'X': 0.00150, 'Y': 0.01994,
         'Z': 0.00077})
SORTED_ENGLISH_FREQUENCIES = blind_distribution(ENGLISH_FREQUENCIES)


def chi_squared(observed_dist, expected_dist):
    """
    Chi-squared test for similarity between two normalised distributions.

    It calculates a deviation term for each item that appears in either
    distribution. Items not appearing in a distribution are assumed to be 0. If
    an item with probability 0 appears a nonzero number of times as an observed
    value, infinity is returned.
    """
    all_entries = set(observed_dist) | set(expected_dist)
    # this is probably mathematically and programmatically bad. But basically in
    # the case where o = e = 0, I just want (o - e) ** 2 / e to be 0, since
    # there is no contribution of this point. if that makes any sense.
    # Anyway, 0^2 / 0 == 0, just ask a differential equations lecturer
    my_div = lambda a, b: 0 if a == 0 else inf if b == 0 else a / b
    return sum(my_div((o - e) ** 2, e) for o, e in
                ((d.get(i, 0) for d in (observed_dist, expected_dist))
                    for i in all_entries))


class Metric:
    """
    A decorator for a function which computes some measure for generated text.
    """
    def __init__(self, measure):
        """
        `measure` should be a function which takes an iterable and computes the
        metric, returning a number
        """
        self.measure = measure

    def __call__(self, text, *args, **kwargs):
        """
        Call the actual function. This also strips punctuation and makes text
        uppercase, follows the principle of least astonishment, I think (eg
        you'd expect ioc(BEE_MOVIE) to not think about spaces).
        """
        return self.measure(strip_punc(text), *args, **kwargs)

    def no_strip(self, text, *args, **kwargs):
        """
        Call the function without stripping punctuation
        """
        return self.measure(text, *args, **kwargs)

    def random(self, num=5000):
        """
        Compute the metric for some randomly generated characters
        """
        return self(random.choice(string.ascii_uppercase) for _ in range(num))

    def english(self):
        """
        Compute the metric for some English plaintext

        Namely, the bee movie script.
        """
        return self(BEE_MOVIE)


@Metric
def ioc(text, domain_size=26):
    """
    Compute the index of coincidence for some text.

    Works for any alphabet, not just letters, though you should then pass a
    correct normalising factor as `domain_size` (and you'd need to call via
    ioc.no_strip())
    """
    # Maps letters to how many times they occur.
    letters = collections.Counter(text)
    # We need to find out how long the text is
    length = sum(letters.values())
    # special case when length is too small for IOC to be defined
    if length < 2:
        return 0
    # Form the actual IOC sum
    ioc_sum = sum(count * (count - 1) for count in letters.values())
    # Don't divide until the very end to minimise floating point problems
    return ioc_sum * domain_size / (length * (length - 1))


@Metric
def frequency_goodness_of_fit(text):
    """
    Compute the goodness of fit with expected English letter frequencies.

    Will do some weird stuff if you call it with no_strip, so probably don't do
    that (unless you already know your text is punctuation free and uppercase,
    in which case, feel free to make this tiny optimisation, but do so at your
    own risk).
    """
    # Maps letters to their frequencies
    letter_dist = normalise(collections.Counter(text))
    return chi_squared(letter_dist, ENGLISH_FREQUENCIES)


@Metric
def blind_frequency_fit(text):
    """
    Compute goodness of fit by comparing blind distributions. This test can be
    applied to any kind of simple polyalphabetic monograph substitution cipher,
    for instance (eg Vigenère, Caesar, keyword substitution, Beaufort...)
    """
    letter_dist = normalise(collections.Counter(text))
    return chi_squared(blind_distribution(letter_dist),
                       SORTED_ENGLISH_FREQUENCIES)


if __name__ == "__main__":
    for metric in ioc, frequency_goodness_of_fit, blind_frequency_fit:
        print(metric.random())
        print(metric.english())
