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

import string
import collections

import argparse

from perm import Perm
from cipher_streamer import CipherStreamer, chunk, BLOCK_DEFAULT, WIDTH_DEFAULT
from util import strip_punc

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
            yield sigma_inverse[a]
        else:
            a_plain = sigma_inverse[a]
            b_plain = tau_inverse[b]
            yield from (a_plain, b_plain)
            transposition = Perm.from_cycle([a_plain, b_plain])
            sigma_inverse = transposition * sigma_inverse
            tau_inverse = transposition * tau_inverse

def permutation_from_key(key):
    """
    Generate a low-level permutation from a key consisting of letters,
    by removing repeated letters and filling in the rest of the
    alphabet going from the last letter. Eg "linustorvalds" as key becomes
    ABCDEFGHIJKLMNOPQRSTUVWXYZ
    LINUSTORVADEFGHJKMPQWXYZBC
    This method is /not/ completely standard. Wikipedia would have you believe
    that you should just chug along with the rest of the alphabet from the first
    letter, but this bleeds huge amounts of information into your permutation,
    as xyz will often map to xyz, whereas here they're basically randomly
    offset. (Wikipedia's example sneakily has a z in the key so you don't notice
    this)

    This function generously strips any punctuation and makes the string
    uppercase, so should be fairly robust on any input.
    """
    mapping = {}
    alphabet = set(string.ascii_uppercase)
    from_iterable = iter(string.ascii_uppercase)
    # use an OrderedDict so as to retain compatibility with 3.6 spec
    key_unique = "".join(collections.OrderedDict.fromkeys(strip_punc(key)))
    # in case of empty key (although that's not a good idea)
    k = 'A'
    for k, a in zip(key_unique, from_iterable):
        mapping[a] = k
        alphabet.remove(k)
    alphabet = sorted(alphabet)
    start_index = 0
    while start_index < len(alphabet) and alphabet[start_index] < k:
        start_index += 1
    for ind, k in enumerate(from_iterable):
        mapping[k] = alphabet[(start_index + ind) % len(alphabet)]
    return Perm(mapping)

def get_args():
    """
    Parse argv
    """
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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
            help="""Print more information - careful you don't use `-` as
                    out_file and pipe to anything.""")
    parser.add_argument(
            "-p", "--preserve", action="store_true",
            help="Preserve punctuation and case in output")
    parser.add_argument(
            "-c", "--compare", action="store_const", const=True,
            help="Output original text to help cryptanalysis")
    parser.add_argument(
            "-l", "--lowercase", action="store_const", const=True,
            help="""Size of blocks to format output into - internal default
                    {}""".format(BLOCK_DEFAULT))
    parser.add_argument(
            "-b", "--block", type=int,
            help="""Size of blocks to format output into - internal default
                    {}""".format(BLOCK_DEFAULT))
    parser.add_argument(
            "-w", "--width", type=int,
            help="""Length of lines to format output into - internal default
                    {}""".format(WIDTH_DEFAULT))
    # have to do a bit of manual checking here - I don't think there's a way to
    # express this kind of dependency in pure ArgumentParser. cf:
    # https://stackoverflow.com/questions/27411268/arguments-that-are-dependent-on-other-arguments-with-argparse
    args = parser.parse_args()
    if args.preserve:
        # here I'm directly accessing the dictionary associated with the
        # returned NameSpace object, for D.R.Y reasons.
        for short_name, arg in (("b", "block"), ("w", "width"),
                                ("c", "compare"), ("l", "lowercase")):
            if vars(args)[arg] is not None:
                parser.error(
                        "-{}/--{} can't be used with -p/--preserve"
                            .format(short_name, arg))
    else:
        for arg, default in (("block", BLOCK_DEFAULT), ("width", WIDTH_DEFAULT),
                             ("compare", False), ("lowercase", False)):
            if vars(args)[arg] is None:
                vars(args)[arg] = default
        if min(args.block, args.width) > 0 and args.width < args.block:
            parser.error("WIDTH should be >= BLOCK")
    return args

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
            process_func = autoperm_encipher
        else:
            args.verbose and print("Deciphering...")
            process_func = autoperm_decipher
        if args.preserve:
            process_func.preserve(args.in_file, args.out_file, sigma, tau)
        else:
            process_func.strip(
                    args.in_file, args.out_file, sigma, tau,
                    block=args.block, width=args.width, compare=args.compare,
                    lowercase=args.lowercase)

if __name__ == "__main__":
    main(get_args())
