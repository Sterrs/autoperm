#                  __
# _____    __ __ _/  |_  ____  ______    ____ _______   _____
# \__  \  |  |  \\   __\/  _ \ \____ \ _/ __ \\_  __ \ /     \
#  / __ \_|  |  / |  | (  <_> )|  |_> >\  ___/ |  | \/|  Y Y  \
# (____  /|____/  |__|  \____/ |   __/  \___  >|__|   |__|_|  /
#      \/                      |__|         \/              \/
# FIGMENTIZE: autoperm

"""
Implementation of the autoperm cipher described in autoperm.tex.

Implementation and specification by the mighty Alastair Horn.
"""

# TODO: try to do something with stripping accents from Unicode characters with
#       unicodedata
# TODO: generally write a couple more tests:
#       - for the top-level functions in this module
#       - add tests to existing suites
#       - integration tests for how well the whole thing works

import string
import random
import itertools
import collections

import argparse

class Perm:
    """
    An object representing a permutation, which can be composed with other
    permutations. This implementation is agnostic to where its elements live, so
    long as they can be put in a dictionary.

    Permutation objects should be treated as immutable. New permutations can be
    obtained by calling methods like inverse() or composing existing
    permutations, which can be achieved by using the overloaded * operator.
    """
    def __init__(self, mapping):
        """
        Create a permutation directly by providing a dictionary map
        """
        self.mapping = mapping

    @classmethod
    def from_cycle(cls, cycle):
        """
        Cycle should be an uppercase string with no repeated letters
        """
        mapping = {}
        for i in range(len(cycle)):
            a = cycle[i]
            b = cycle[(i + 1) % len(cycle)]
            mapping[a] = b
        return cls(mapping)

    @classmethod
    def random(cls, domain):
        """
        Generate a pseudorandom permutation
        """
        outputs = list(domain)
        random.shuffle(outputs)
        return cls(dict(zip(domain, outputs)))

    def disjoint_cycle_decomposition(self):
        """
        Get a list of lists which is the disjoint cycle decomposition. _DON'T_
        include 1-cycles, so that more can be inferred about cycle types across
        different domains from this decomposition.
        """
        # use a set for amortised O(1) lookup
        remaining = set(self.mapping)
        decomposition = []
        while remaining:
            a = remaining.pop()
            cycle = [a]
            b = self[a]
            # this could of course be done beautifully with the walrus operator,
            # but I'm trying to keep my Ubuntu-using fans happy
            while b != a:
                remaining.remove(b)
                cycle.append(b)
                b = self[b]
            if len(cycle) > 1:
                decomposition.append(cycle)
        return decomposition

    def inverse(self):
        """
        Create the inverse of a permutation
        """
        return self.__class__({v: k for k, v in self.mapping.items()})

    def __str__(self):
        """
        Convert to disjoint cycle decomposition string
        """
        return "".join("({})".format(" ".join(map(str, cycle))) for cycle in
                self.disjoint_cycle_decomposition())

    def __repr__(self):
        """
        Show the underlying dictionary object
        """
        return "{}({})".format(self.__class__.__name__, self.mapping)

    def __getitem__(self, item):
        """
        Use lookup syntax to apply the permutation to an element.

        Uses the convention that an unknown item is mapped to itself.
        """
        return self.mapping.get(item, item)

    def __mul__(self, other):
        """
        Compose permutation with another. It's not obvious how the domain of the
        resulting permutation should be inferred, but I'm using the convention
        that the domain stays as big as possible, which hopefully avoids
        forgetting anything important
        """
        return self.__class__({a: self[other[a]]
                               for a in set(self.mapping) | set(other.mapping)})

    def __pow__(self, n):
        """
        Exponent of a permutation, in the standard group-theoretic sense.
        Probably it's O(k * log(n))-ish where k is the size of the domain, and n
        is the exponent, as it uses exponentiation by squaring.

        Supports negative exponents in the standard inverse sense.
        """
        if n < 0:
            return self.inverse() ** (-n)
        # Some hardcoded cases to avoid faffing around too much in the leaves of
        # the tree (and lets me write ** 2 in the recursive step, so the
        # auxiliary variable gets brushed under the recursion)
        if n == 0:
            return self.__class__({})
        if n == 1:
            return self
        if n == 2:
            return self * self
        exp_by_sqr = (self ** (n // 2)) ** 2
        if n & 1:
            return self * exp_by_sqr
        return exp_by_sqr

    def __eq__(self, other):
        """
        Test for equality: all items map to the same thing.
        """
        return (all(sa == other[a] for a, sa in self.mapping.items())
                and all(oa == self[a] for a, oa in other.mapping.items()))

class CipherStreamer:
    """
    Context to stream a file object through a function and write it to
    an output, exposing the input as only uppercase letters. This class takes
    care of case correction and punctuation.

    This is implemented as a decorator, that takes the arguments `in_file` and
    `out_file`, a readable and writeable file respectively. Any further
    arguments are passed on to the function being decorated.

    Obviously not very useful if you're doing serious cryptography, but I think
    it's more aesthetic to keep punctuation in (and it makes for an easy way to
    lower the difficulty of cryptanalysis for cipher challenge type things).

    If more output letters are produced than there were input letters, the extra
    letters are all written as they are, with no separation.

    At the end, all remaining punctuation is written to the output file. This is
    useful because for instance it means that the last trailing newline (which
    is present in any file made by a sane person) will be written as output.
    """
    def __init__(self, func):
        """
        Func should be a generator with first positional argument an iterable of
        alphabetic characters, and further arguments passed through *args,
        **kwargs. Func should yield alphabetic characters to be written.
        """
        self.func = func

    # TODO: do this better (more lazily), with itertools or something. As it
    #       stands this could easily just be written as a function returning a
    #       closure.
    #       I think we have to ask for func to be implemented as a coroutine to
    #       do this nicely
    def __call__(self, in_file, out_file, *args, **kwargs):
        """
        This is what happens when people actually call the function
        """
        in_file_1, in_file_2 = itertools.tee(
                iter(lambda: in_file.read(1), ""))
        output = self.func((c.upper() for c in in_file_1 if c.isalpha()),
                            *args, **kwargs)
        for c in output:
            punc = ' '
            for punc in in_file_2:
                if punc.isalpha():
                    break
                out_file.write(punc)
            if not punc.isalpha():
                out_file.write(c)
            elif punc.isupper():
                out_file.write(c.upper())
            else:
                out_file.write(c.lower())
        for punc in in_file_2:
            if not punc.isalpha():
                out_file.write(punc)

def chunk(iterable, size, fillvalue=None):
    """
    Split an iterable into chunks of size `size`. Padded with `fillvalue` if
    necessary.
    """
    return itertools.zip_longest(*[iter(iterable)] * size, fillvalue=fillvalue)

@CipherStreamer
def autoperm_encipher(plaintext, sigma, tau):
    """
    Encrypt
    """
    for a, b in chunk(plaintext, 2):
        if b is None:
            yield sigma[a]
        else:
            yield from (sigma[a], tau[b])
            transposition = Perm.from_cycle([a, b])
            sigma *= transposition
            tau *= transposition

@CipherStreamer
def autoperm_decipher(ciphertext, sigma, tau):
    """
    Decrypt
    """
    sigma_inverse = sigma.inverse()
    tau_inverse = tau.inverse()
    for a, b in chunk(ciphertext, 2):
        if b is None:
            yield sigma_inverse[b]
        else:
            a_plain = sigma_inverse[a]
            b_plain = tau_inverse[b]
            yield from (a_plain, b_plain)
            transposition = Perm.from_cycle([a_plain, b_plain])
            sigma_inverse = transposition * sigma_inverse
            tau_inverse = transposition * tau_inverse

def permutation_from_key(key):
    """
    Generate a low-level permutation from a key consisting of letters
    """
    mapping = {}
    alphabet = set(string.ascii_uppercase)
    from_iterable = iter(string.ascii_uppercase)
    # use an OrderedDict so as to retain compatibility with 3.6 spec
    key_unique = "".join(
            collections.OrderedDict.fromkeys(
                c.upper() for c in key if c.isalpha()))
    # these for loops and zips together are sure to exhaust the alphabet in the
    # way I want, but it's not very easy to follow. TODO: rewrite
    for k, a in zip(key_unique, from_iterable):
        mapping[a] = k
        alphabet.remove(k)
    for k, a in zip(sorted(alphabet), from_iterable):
        mapping[a] = k
    return Perm(mapping)

def get_args():
    """
    Parse argv
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
            "in_file", type=argparse.FileType("r"), default="-", nargs="?",
            help="Input file (plaintext or ciphertext)")
    parser.add_argument(
            "out_file", type=argparse.FileType("w"), default="-", nargs="?",
            help="Output file (plaintext or ciphertext)")
    key = parser.add_mutually_exclusive_group(required=True)
    key.add_argument(
        "-r", "--random", action="store_true",
        help="Generate random keys (hard to remember)")
    key.add_argument(
        "-k", "--keys", nargs=2, metavar=("SIGMA", "TAU"),
        help="Give two keywords to convert into permutations sigma, tau")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
            "-e", "--encrypt", action="store_true",
            help="Perform encryption")
    action.add_argument(
            "-d", "--decrypt", action="store_true",
            help="Perform decryption")
    parser.add_argument(
            "-v", "--verbose", action="store_true",
            help="""Print more information - careful you don't use - as out_file
                    and pipe to anything.""")
    return parser.parse_args()

def main(args):
    """
    Main function
    """
    if args.random:
        # Generate random permutation for initial sigma, tau
        sigma = Perm.random(string.ascii_uppercase)
        tau = Perm.random(string.ascii_uppercase)
    else:
        sigma, tau = map(permutation_from_key, args.keys)
    args.verbose and print("sigma = {}".format(sigma))
    args.verbose and print("tau   = {}".format(tau))
    with args.in_file, args.out_file:
        if args.encrypt:
            args.verbose and print("Enciphering...")
            autoperm_encipher(args.in_file, args.out_file, sigma, tau)
        else:
            args.verbose and print("Deciphering...")
            autoperm_decipher(args.in_file, args.out_file, sigma, tau)

if __name__ == "__main__":
    main(get_args())
