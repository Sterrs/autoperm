

def gen_file(f):
    """Generate the characters in a file one by one"""
    return iter(lambda: f.read(1), "")


def strip_gen(gen):
    """Remove all but the letters and make them uppercase"""
    return (c.upper() for c in gen if c.isalpha())
