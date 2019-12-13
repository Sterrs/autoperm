"""
Cipher streamer class
"""

import itertools

# Block default of 4 makes much more sense :P
BLOCK_DEFAULT = 4
WIDTH_DEFAULT = 80

def chunk(iterable, size, fillvalue=None):
    """
    Split an iterable into chunks of size `size`. Padded with `fillvalue` if
    necessary.
    """
    return itertools.zip_longest(*[iter(iterable)] * size, fillvalue=fillvalue)


def get_lines(iterable, block, width):
    """
    Convert some text into regular blocks of characters, wrapped after
    a certain length.
    If block <= 0, do not insert spaces
    If width <= 0, do not insert newlines
    """
    if min(block, width) > 0 and width < block:
        raise ValueError("`width` should be >= `block`")

    # Each of the four cases is expected to produce an iterable `lines`,
    # consisting of iterables of strings to be joined and written as lines
    # to out_file.
    if block <= 0:
        if width <= 0:
            lines = iterable,
        else:
            # chunk output into lines of length `width`
            lines = chunk(iterable, width, "")
    else:
        # chunk the output into blocks of size `block`
        chunks = chunk(iterable, block, "")
        # add a space after each block
        chunks_spaced = map(itertools.chain.from_iterable,
                            zip(chunks, itertools.repeat(" ")))
        if width <= 0:
            # just write all the blocks
            lines = itertools.chain.from_iterable(chunks_spaced),
        else:
            blocks_per_line = (width + 1) // (block + 1)
            # split blocks into lines
            lines = map(itertools.chain.from_iterable,
                        chunk(chunks_spaced, blocks_per_line, ""))

    return lines


class CipherStreamer:
    """
    Context to stream a file object through a function and write it to
    an output, exposing the input as only uppercase letters. This class
    can handle case correction and punctuation, if the caller wants it to.

    This is implemented as a decorator, that takes the arguments `in_file` and
    `out_file`, a readable and writeable file respectively. A keyword argument
    `preserve` is also understood, and then depending on the value of that, the
    further keyword arguments `block` and `width` may be absorbed - see method
    documentation. Any further arguments are passed on to the function being
    decorated.

    (Make sure your function doesn't have any arguments with the same name as
    these!)

    Obviously the preservative functionality isn't very useful if you're doing
    serious cryptography, but I think it's more aesthetic to keep punctuation in
    (and it makes for an easy way to lower the difficulty of cryptanalysis for
    cipher challenge type things).

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

    def __call__(self, *args, preserve=False, block=None, width=None, compare=False, **kwargs):
        """
        This is what happens when people actually call the function. It
        dispatches to the appropriate method.
        """
        if preserve:
            if block is not None or width is not None:
                raise ValueError(
                        "Preserve mode doesn't understand block or width")
            self.preserve(*args, **kwargs)
        else:
            if block is None:
                block = BLOCK_DEFAULT
            if width is None:
                width = WIDTH_DEFAULT
            self.strip(*args, block=block, width=width, compare=compare, **kwargs)

    def strip(self, in_file, out_file, *args, compare=False,
              block=BLOCK_DEFAULT, width=WIDTH_DEFAULT, **kwargs):
        """
        Strip all punctuation from the output, convert output to uppercase, and
        format the output into blocks of size `block`, with lines wrapped to
        length `width`. If width is <= 0, no wrapping is done. If block is <= 0,
        no spaces are inserted.

        Of course you could simulate the case with width <= 0, block > 0 with
        the case width > 0, block <= 0 (and vice versa). But I think it's a nice
        courtesy to support both.

        It is *excruciatingly* lazy, to the point of illegibility. But I think
        it's fun :)
        """

        if compare:
            # This is probably really inefficient but I don't know enough about
            # itertools to fix it
            input_text, plaintext = itertools.tee((c.upper() for c in iter(lambda: in_file.read(1), "") if c.isalpha()))
        else:
            input_text = (c.upper() for c in iter(lambda: in_file.read(1), "") if c.isalpha())

        plain_lines = ()
        if compare:
            plain_lines = get_lines(plaintext, block, width)

        output = self.func(input_text, *args, **kwargs)
        lines = get_lines(output, block, width)

        # Just strip of any extra spaces at this stage rather than worrying
        # about removing them earlier.
        for line, plain in itertools.zip_longest(lines, plain_lines, fillvalue=None):
            if compare and plain is not None:
                out_file.write("".join(plain).strip().upper())
                out_file.write("\n")
            out_file.write("".join(line).strip().upper())
            out_file.write("\n")
            compare and out_file.write("\n")

    # TODO: do this better (more lazily), with itertools or something. As it
    #       stands this could easily just be written as a function returning a
    #       closure.
    #       I think we have to ask for func to be implemented as a coroutine to
    #       do this nicely
    def preserve(self, in_file, out_file, *args, **kwargs):
        """
        Restore punctuation and case after the generator.

        If more output letters are produced than there were input letters, the
        extra letters are all written as they are, with no separation.

        At the end, all remaining punctuation is written to the output file.
        This is useful because for instance it means that the last trailing
        newline (which is present in any file made by a sane person) will be
        written as output.
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
