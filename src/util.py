"""
Utilities for use throughout. Mostly to do with stripping text and reading
files.
"""

def file_chars(f):
    """
    Generate the characters in a file one by one
    """
    return iter(lambda: f.read(1), "")

def strip_punc(gen):
    """
    Remove all but the letters and make them uppercase
    """
    return (c.upper() for c in gen if c.isalpha())
