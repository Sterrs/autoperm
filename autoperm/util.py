# vim: ts=4 sw=0 sts=-1 et ai tw=80

"""
Utilities for use throughout. Mostly to do with stripping text and reading
files.
"""

# TODO: probably it's faster to just read it all into memory. We're almost
#       invariably dealing with tiny, tiny files.
def file_chars(file):
    """
    Generate the characters in a file one by one
    """
    return iter(lambda: file.read(1), "")


# TODO: try to do something with stripping accents from Unicode characters with
#       unicodedata. Basically the mixing and matching of str.isalphas and
#       str.uppers means that because Python is very good at
#       internationalisation, if you have plaintext or keys with wéïrd unicode
#       characters in, things will probably break.
#
#       An improvement for now would be to just re-write this explicitly talking
#       about ASCII characters a-z and A-Z.
def strip_punc(gen):
    """
    Remove all but the letters and make them uppercase
    """
    return map(str.upper, filter(str.isalpha, gen))
