"""
Cipher streamer class
"""

import itertools

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

    It is perhaps worth mentioning that it is still perfectly possible to access
    the underlying generator:
    >>> @CipherStreamer
    ... def my_cipher(text):
    ...     pass
    >>> my_cipher.func
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
