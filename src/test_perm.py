"""
Unit tests for Perm in autoperm.py.

This contains an inordinate library of permutations that it runs some sanity
checks on. It becomes even more inordinate when some combinatorics gets
involved, but it helps my peace of mind a lot. For reference, when I run
$ pypy3 -m unittest -v
it takes about 4-6 seconds to finish.
"""

import unittest

import itertools

from functools import reduce
from operator import mul
from random import sample
from collections import OrderedDict

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
                *(Perm.from_cycle(range(j, j + i)) for i in range(4, 9)
                                                   for j in range(9 - i)),
                *(Perm.from_cycle(range(j, j + i)[::-1]) for i in range(2, 9)
                                                         for j in range(9 - i)
                                                         ),
                self.operm, self.perm6]
        # add some more random permutations to hopefully catch more edge cases,
        # but keep them in a separate list so I can also access a deterministic
        # list of permutations that I can guarantee properties of
        self.perms = [
                *self.reg_perms,
                *(Perm.random(range(i)) for i in range(4, 20))]
        for _ in range(10):
            a, b = sample(self.perms, 2)
            self.perms.append(a * b)

    def test_is_permutation(self):
        for g in self.perms:
            self.assertTrue(g.is_permutation())
        self.assertFalse(Perm({1: 2, 2: 2}).is_permutation())
        self.assertFalse(Perm({1: 2, 2: 3}).is_permutation())

    def test_eq(self):
        for g in self.perms:
            self.assertEqual(g, g)
            self.assertEqual(g, Perm(g.mapping))
            self.assertEqual(g, Perm(g.mapping.copy()))
            self.assertNotEqual(g, Perm({**g.mapping, -1: -2}))
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
        self.assertEqual(Perm.from_cycle([1] * 2), Perm())
        self.assertEqual(Perm.from_cycle([1] * 3), Perm())
        self.assertEqual(Perm.from_cycle([1] * 4), Perm())
        self.assertEqual(Perm.from_cycle([2, 3, 1]),
                         self.perm3c)
        self.assertEqual(Perm.from_cycle([3, 2, 1]),
                         Perm({1: 3, 2: 1, 3: 2}))
        for i in range(20):
            for j in range(1, 5):
                self.assertEqual(Perm.from_cycle(list(range(i)) * j),
                                 Perm.from_cycle(range(i)))
                self.assertTrue(
                        Perm.from_cycle(list(range(i)) * j).is_permutation())

    def test_random(self):
        # check valid permutations are given
        for i in range(100):
            self.assertTrue(Perm.random(range(i)).is_permutation)

    def test_disjoint_cycle_decomposition(self):
        self.assertEqual(Perm().disjoint_cycle_decomposition_stable(), [])
        self.assertEqual(self.perm6.disjoint_cycle_decomposition_stable(),
                         [[1, 2], [4, 5, 6]])
        self.assertEqual(self.perm3c.disjoint_cycle_decomposition_stable(),
                         [[1, 2, 3]])
        # reconstruct permutations as a cycle composition
        for g in self.perms:
            self.assertEqual(
                    reduce(mul,
                           map(Perm.from_cycle,
                               g.disjoint_cycle_decomposition_unstable()),
                           Perm()),
                    g)
            self.assertEqual(
                    reduce(mul,
                           map(Perm.from_cycle,
                               g.disjoint_cycle_decomposition_stable()),
                           Perm()),
                    g)

    def test_inverse(self):
        for g in self.perms:
            self.assertEqual(g.inverse().inverse(), g)
        for g in self.operm, self.permoc, self.perm1c, self.perm2c:
            self.assertEqual(g.inverse(), g)
            self.assertTrue(g.inverse().is_permutation())
        # standard inverse formula works
        for g, h in itertools.product(self.perms, self.perms):
            self.assertEqual((g * h).inverse(), h.inverse() * g.inverse())
        self.assertEqual(Perm.from_cycle([3, 2, 1]).inverse(), self.perm3c)

    def test_comp(self):
        for g in self.perms:
            self.assertEqual(g * g.inverse(), self.operm)
        for g, h in itertools.product(self.perms, self.perms):
            self.assertTrue((g * h).is_permutation())
            # conjugates should preserve cycle type
            conj = h * g * h.inverse()
            self.assertCountEqual(
                    list(map(len, g.disjoint_cycle_decomposition_unstable())),
                    list(map(len,
                             conj.disjoint_cycle_decomposition_unstable())))
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
            prod = self.operm
            for n in range(10):
                self.assertTrue((g ** n).is_permutation())
                self.assertEqual(g ** n, prod)
                self.assertEqual(g ** (-n), prod.inverse())
                prod *= g
            # check if cyclic subgroup generated by g is abelian :)
            for a in range(-10, 10):
                for b in range(-10, 10):
                    self.assertEqual(g ** a * g ** b, g ** (a + b))
            self.assertEqual(g ** -1, g.inverse())
            # check if the order divides the LCM of cycle lengths
            order = reduce(mul,
                           map(len,
                               g.disjoint_cycle_decomposition_unstable()),
                           1)
            self.assertEqual(g ** order, self.operm)
        self.assertEqual(Perm.from_cycle(range(10)) ** 9,
                         Perm.from_cycle(range(10)).inverse())

    def test_lookup(self):
        for g in self.perms:
            self.assertIsNone(g[None])
            self.assertEqual(g["xyz"], "xyz")
            self.assertEqual(g[-1], -1)
            for item in g.mapping:
                self.assertEqual(g.mapping[item], g[item])

    def test_str(self):
        for g in self.perms:
            str(g)
        self.assertEqual(str(Perm()), "Id"),
        self.assertEqual(str(self.perm2c), "(1 2)")
        self.assertEqual(str(self.perm3c), "(1 2 3)")
        self.assertEqual(str(self.perm6), "(1 2)(4 5 6)")

    # The following tests are for string representations. They therefore use
    # OrderedDicts, so that this program is compatible with as much of Python 3
    # as possible, seeing as dictionary order preservation was only added to the
    # spec in 3.7.
    def test_repr(self):
        for g in self.perms:
            repr(g)
        self.assertEqual(repr(Perm(OrderedDict(((1, 2), (2, 1))))),
                         "Perm(OrderedDict([(1, 2), (2, 1)]))")
        self.assertEqual(repr(Perm()),
                         "Perm({})")

    def test_table_format(self):
        for g in self.perms:
            g.table_format()
        self.assertEqual(Perm().table_format(),
                         "Id\n")
        self.assertEqual(Perm(OrderedDict(((1, 2), (2, 1)))).table_format(),
                         "1 2\n2 1")
        self.assertEqual(Perm(OrderedDict(((100, 2), (2, 100)))).table_format(),
                         "100   2\n  2 100")

if __name__ == "__main__":
    unittest.main()
