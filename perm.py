"""
Permutation class
"""

import random

class Perm:
    """
    An object representing a permutation, which can be composed with other
    permutations. This implementation is agnostic to where its elements live, so
    long as they can be put in a dictionary.

    Permutation objects should be treated as immutable. New permutations can be
    obtained by calling methods like inverse() or composing existing
    permutations, which can be achieved by using the overloaded * operator.

    If you instantiate via __init__, this class assumes that you're a grown-up
    and you've given it a mapping that is a bijection. If you can't be sure,
    feel free to check with .is_permutation().
    """
    def __init__(self, mapping={}):
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

    def is_permutation(self):
        """
        Simple method that checks if this is a permutation. This method should
        be robust as keys in the given mapping are supposed to be distinct.
        """
        return set(self.mapping.keys()) == set(self.mapping.values())

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
        return type(self)({v: k for k, v in self.mapping.items()})

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
        return "{}({})".format(type(self).__name__, self.mapping)

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
        return type(self)({a: self[other[a]]
                           for a in set(self.mapping) | set(other.mapping)})

    def __pow__(self, n):
        """
        Exponent of a permutation, in the standard group-theoretic sense.
        Probably it's O(k * log(n))-ish where k is the size of the domain, and n
        is the exponent, as it uses exponentiation by squaring.

        Possibly it's worth thinking about the asymptotic improvement brought by
        calculating the order of the permutation and taking n mod ord(g) (in
        fact asymptotically the time is then independent of n) but this is
        probably too theoretical to be useful.

        Supports negative exponents in the standard inverse sense.
        """
        if n < 0:
            return self.inverse() ** (-n)
        # Some hardcoded cases to avoid faffing around too much in the leaves of
        # the tree (and lets me write ** 2 in the recursive step, so the
        # auxiliary variable gets brushed under the recursion)
        if n == 0:
            return type(self)({})
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

