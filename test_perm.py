"""
Unit tests for Perm in autoperm.py
"""

import unittest

import itertools

from functools import reduce
from operator import mul

from perm import Perm

class TestPerm(unittest.TestCase):
    def setUp(self):
        self.perm6 = Perm({1: 2, 2: 1, 3: 3, 4: 5, 5: 6, 6: 4})
        self.operm = Perm({})
        self.permoc = Perm.from_cycle([])
        self.perm1c = Perm.from_cycle([1])
        self.perm2c = Perm.from_cycle([1, 2])
        self.perm3c = Perm.from_cycle([1, 2, 3])
        # huge list of hopefully lots of different kinds of permutation covering
        # lots of edge cases
        self.reg_perms = [
                self.permoc, self.perm1c, self.perm2c, self.perm3c,
                *[Perm.from_cycle(range(i)) for i in range(4, 11)],
                *[Perm.from_cycle(range(i)[::-1]) for i in range(2, 11)],
                self.operm, self.perm6]
        # add some more random permutations to hopefully catch more edge cases,
        # but keep them in a separate list so I can also access a deterministic
        # list of permutations that I can guarantee properties of
        self.perms = [
                *self.reg_perms,
                *[Perm.random(range(i)) for i in range(4, 20)]]

    def test_eq(self):
        for g in self.perms:
            self.assertEqual(g, g)
            self.assertEqual(g, Perm(g.mapping))
            self.assertEqual(g, Perm(g.mapping.copy()))
        self.assertEqual(self.perm6, Perm({1: 2, 2: 1, 4: 5, 5: 6, 6: 4}))
        self.assertEqual(Perm({1: 2, 2: 1}), Perm({2: 1, 1: 2}))
        self.assertEqual(Perm({1: 2, 2: 1, 3: 3}), Perm({2: 1, 1: 2, 4: 4}))
        self.assertEqual(self.permoc, self.perm1c)
        self.assertEqual(self.permoc, self.operm)
        self.assertEqual(self.perm1c, self.operm)
        self.assertEqual(self.operm, Perm({1: 1}))
        self.assertEqual(self.operm, Perm({None: None}))
        for g, h in itertools.combinations(
                [p for p in self.reg_perms if len(p.mapping) > 2], 2):
            self.assertNotEqual(g, h)

    def test_from_cycle(self):
        self.assertEqual(self.permoc, self.operm)
        self.assertEqual(self.perm1c, self.operm)
        self.assertEqual(self.perm2c, Perm({1: 2, 2: 1}))
        self.assertEqual(self.perm3c, Perm({1: 2, 2: 3, 3: 1}))
        self.assertEqual(Perm.from_cycle([2, 3, 1]),
                         self.perm3c)
        self.assertEqual(Perm.from_cycle([3, 2, 1]),
                         Perm({1: 3, 2: 1, 3: 2}))

    def test_random(self):
        # check valid permutations are given
        for i in range(20):
            g = Perm.random(range(i))
            self.assertCountEqual(g.mapping.keys(), g.mapping.values())
            self.assertEqual(set(g.mapping), set(range(i)))

    def test_dcd(self):
        self.assertCountEqual([tuple(sorted(cycle))
                               for cycle in
                                   self.perm6.disjoint_cycle_decomposition()],
                              [(1, 2), (4, 5, 6)])
        self.assertEqual([tuple(sorted(cycle))
                          for cycle in
                              self.perm3c.disjoint_cycle_decomposition()],
                         [(1, 2, 3)])

    def test_inverse(self):
        for g in self.perms:
            self.assertEqual(g.inverse().inverse(), g)
        for g in self.operm, self.permoc, self.perm1c, self.perm2c:
            self.assertEqual(g.inverse(), g)
        # standard inverse formula works
        for g, h in itertools.product(self.perms, self.perms):
            self.assertEqual((g * h).inverse(), h.inverse() * g.inverse())
        self.assertEqual(Perm.from_cycle([3, 2, 1]).inverse(), self.perm3c)

    def test_comp(self):
        for g in self.perms:
            self.assertEqual(g * g.inverse(), self.operm)
        # conjugates should preserve cycle type
        for g, h in itertools.product(self.perms, self.perms):
            conj = h * g * h.inverse()
            self.assertCountEqual(
                    list(map(len, g.disjoint_cycle_decomposition())),
                    list(map(len, conj.disjoint_cycle_decomposition())))
        # associativity of composition
        for g, h, k in itertools.product(*[self.perms] * 3):
            self.assertEqual((g * h) * k, g * (h * k))
        self.assertEqual(Perm.from_cycle([4, 5, 6]) * self.perm6,
                         Perm({1: 2, 2: 1, 4: 6, 5: 4, 6: 5}))
        self.assertEqual(Perm.from_cycle([1, 2]) * Perm.from_cycle([2, 3]),
                         Perm.from_cycle([1, 2, 3]))
        self.assertEqual(self.perm3c ** 3, self.operm)

    def test_pow(self):
        # test if pow behaves as expected with conjugates
        for g, h in itertools.product(self.perms, self.perms):
            for n in range(10):
                self.assertEqual(h * g ** n * h.inverse(),
                                 (h * g * h.inverse()) ** n)
        for g in self.perms:
            # check if iterative calculation agrees
            for n in range(10):
                prod = self.operm
                for i in range(n):
                    self.assertEqual(g ** i, prod)
                    self.assertEqual(g ** (-i), prod.inverse())
                    prod *= g
            # check if cyclic subgroup generated by g is abelian :)
            for a in range(-10, 10):
                for b in range(-10, 10):
                    self.assertEqual(g ** a * g ** b, g ** (a + b))
            self.assertEqual(g ** -1, g.inverse())
            # check if the order divides the LCM of cycle lengths
            order = reduce(mul, map(len, g.disjoint_cycle_decomposition()), 1)
            self.assertEqual(g ** order, self.operm)
        self.assertEqual(self.perms[10] ** 9,
                         self.perms[10].inverse())

    def test_call(self):
        for g in self.perms:
            self.assertIsNone(g[None])
            self.assertEqual(g["xyz"], "xyz")
            self.assertEqual(g[-1], -1)
            for item in g.mapping:
                self.assertEqual(g.mapping[item], g[item])

if __name__ == "__main__":
    unittest.main()
