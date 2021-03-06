import unittest
from copy import copy

from construct.lib.container import Container, FlagsContainer, ListContainer

import random
def shuffled(alist):
    a = list(alist)
    random.shuffle(a)
    return a
from random import randint


class TestContainer(unittest.TestCase):

    def test_ctor_from_dict(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        d = Container(c)
        self.assertEqual(c, d)

    def test_getattr(self):
        c = Container(a=1)
        self.assertEqual(c["a"], 1)
        self.assertEqual(c.a, 1)

    def test_getattr_missing(self):
        c = Container(a=1)
        self.assertRaises(AttributeError, lambda: c.unknownkey)
        self.assertRaises(KeyError, lambda: c["unknownkey"])

    def test_setattr(self):
        c = Container()
        c.a = 1
        self.assertEqual(c.a, 1)
        self.assertEqual(c["a"], 1)
        c["a"] = 2
        self.assertEqual(c.a, 2)
        self.assertEqual(c["a"], 2)

    def test_delattr(self):
        c = Container(a=1)
        del c.a
        self.assertFalse("a" in c)
        self.assertRaises(AttributeError, lambda: c.a)
        self.assertRaises(KeyError, lambda: c["a"])
        self.assertEqual(c, Container())

    def test_update_from_dict(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        d = Container()
        d.update(c)
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)
        self.assertEqual(d.c, 3)
        self.assertEqual(d.d, 4)
        self.assertEqual(c, d)
        self.assertEqual(c.items(), d.items())

    def test_update_from_list(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        d = Container()
        d.update([("a",1),("b",2),("c",3),("d",4)])
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)
        self.assertEqual(d.c, 3)
        self.assertEqual(d.d, 4)
        self.assertEqual(c, d)
        self.assertEqual(c.items(), d.items())

    def test_items(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        self.assertEqual(c.keys(), ["a","b","c","d"])
        self.assertEqual(c.values(), [1,2,3,4])
        self.assertEqual(c.items(), [("a",1),("b",2),("c",3),("d",4)])

    def test_iters(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        self.assertEqual(list(c.iterkeys()), ["a","b","c","d"])
        self.assertEqual(list(c.itervalues()), [1,2,3,4])
        self.assertEqual(list(c.iteritems()), [("a",1),("b",2),("c",3),("d",4)])

    def test_order_randomized(self):
        print("WARNING: this test is randomized and may not be reproducible")
        c = Container()
        while True:
            words = [("".join(chr(randint(65, 97)) for _ in range(randint(3,7))), i) for i in range(20)]
            if words != list(dict(words).keys()):
                break
        c.update(words)
        self.assertEqual([k for k, _ in words], list(c.keys()))

    def test_eq(self):
        c = Container(a=1)(b=2)(c=3)(d=4)(e=5)
        d = Container(a=1)(b=2)(c=3)(d=4)(e=5)
        self.assertEqual(c, d)

    def test_ne_wrong_order(self):
        print("WARNING: dict randomizes key order so this test may fail unexpectedly if the order is correct by chance.")
        c = Container(a=1,b=2,c=3,d=4,e=5,f=6,g=7,h=8,i=9,j=10,k=11,l=12,m=13,n=14)
        d = Container(shuffled(c.items()))
        self.assertNotEqual(c, d)

    def test_ne_wrong_type(self):
        c = Container(a=1)
        d = [("a", 1)]
        self.assertNotEqual(c, d)

    def test_ne_wrong_key(self):
        c = Container(a=1)
        d = Container(b=1)
        self.assertNotEqual(c, d)

    def test_ne_wrong_value(self):
        c = Container(a=1)
        d = Container(a=2)
        self.assertNotEqual(c, d)

    def test_copy(self):
        c = Container(a=1)
        d = c.copy()
        self.assertEqual(c, d)
        self.assertTrue(c is not d)

    def test_copy_module(self):
        c = Container(a=1)
        d = copy(c)
        self.assertEqual(c, d)
        self.assertTrue(c is not d)

    def test_bool_false(self):
        c = Container()
        self.assertFalse(c)

    def test_bool_false_regression(self):
        # recursion_lock() used to leave private keys
        c = Container()
        str(c); repr(c)
        self.assertFalse(c)

    def test_bool_true(self):
        c = Container(a=1)
        self.assertTrue(c)

    def test_in(self):
        c = Container(a=1)
        self.assertTrue("a" in c)

    def test_not_in(self):
        c = Container()
        self.assertTrue("a" not in c)

    def test_repr(self):
        c = Container(a=1)(b=2)(c=3)
        self.assertEqual(repr(c), "Container(a=1)(b=2)(c=3)")

    def test_repr_empty(self):
        c = Container()
        self.assertEqual(repr(c), "Container()")
        self.assertEqual(eval(repr(c)), c)

    def test_repr_nested(self):
        c = Container(a=1)(b=2)(c=Container())
        self.assertEqual(repr(c), "Container(a=1)(b=2)(c=Container())")
        self.assertEqual(eval(repr(c)), c)
    
    def test_repr_recursive(self):
        c = Container(a=1)(b=2)
        c.c = c
        self.assertEqual(repr(c), "Container(a=1)(b=2)(c=<recursion detected>)")

    def test_str(self):
        c = Container(a=1)(b=2)(c=3)
        self.assertEqual(str(c), "Container: \n    a = 1\n    b = 2\n    c = 3")

    def test_str_empty(self):
        c = Container()
        self.assertEqual(str(c), "Container: ")

    def test_str_nested(self):
        c = Container(a=1)(b=2)(c=Container())
        self.assertEqual(str(c), "Container: \n    a = 1\n    b = 2\n    c = Container: ")
    
    def test_str_recursive(self):
        c = Container(a=1)(b=2)
        c.c = c
        self.assertEqual(str(c), "Container: \n    a = 1\n    b = 2\n    c = <recursion detected>")
    
    def test_dict_arg(self):
        print("NOTE: dicts do not preserve order while eq does check it (by default).")
        print("However, only one entry is in order.")
        c = Container({'a': 1})
        d = Container(a=1)
        self.assertEqual(c, d)
        self.assertTrue(c.__eq__(d, skiporder=True))

    def test_multiple_dict_args(self):
        print("NOTE: dicts do not preserve order while eq does check it (by default).")
        c = Container({'a': 1, 'b': 42}, {'b': 2})
        d = Container(a=1, b=2)
        # self.assertEqual(c, d)
        self.assertTrue(c.__eq__(d, skiporder=True))

    def test_dict_and_kw_args(self):
        print("NOTE: dicts do not preserve order while eq does check it (by default).")
        c = Container({'b': 42, 'c': 43}, {'a': 1, 'b': 2, 'c': 4}, c=3, d=4)
        d = Container(a=1, b=2, c=3, d=4)
        # self.assertEqual(c, d)
        self.assertTrue(c.__eq__(d, skiporder=True))


class TestFlagsContainer(unittest.TestCase):

    def test_str(self):
        c = FlagsContainer(a=True, b=False, c=True, d=False)
        str(c)
        repr(c)

    def test_eq(self):
        c = FlagsContainer(a=True, b=False, c=True, d=False)
        d = FlagsContainer(a=True, b=False, c=True, d=False)
        self.assertEqual(c, d)


class TestListContainer(unittest.TestCase):

    def test_str(self):
        l = ListContainer(range(5))
        str(l)
        repr(l)

    def test_recursive_str(self):
        l = ListContainer(range(5))
        l.append(l)
        str(l)
        repr(l)

