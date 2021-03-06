#!/usr/bin/env python
import yaml
import unittest
from salt_check import Tester
#sys.path.append(os.path.abspath(sys.path[0]) + '/../')

# Note: the order tests are run is arbitrary!

class MyClass(unittest.TestCase):

    def setUp(self):
        mt = Tester()

    def tearDown(self):
        pass

    def test_1_assert_equal(self):
        val = Tester.assert_equal(True, True)
        self.assertEqual(True, val)

    def test_2_assert_equal(self):
        val = Tester.assert_equal(True, False)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_3_assert_equal(self):
        val = Tester.assert_equal(False, False)
        self.assertEqual(True, val)

    def test_1_assert_not_equal(self):
        val = Tester.assert_not_equal(True, False)
        self.assertEqual(True, val)

    def test_2_assert_not_equal(self):
        val = Tester.assert_not_equal(True, True)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_3_assert_not_equal(self):
        val = Tester.assert_not_equal(False, False)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_1_assert_true(self):
        val = Tester.assert_true(True)
        self.assertEqual(True, val)

    def test_2_assert_true(self):
        val = Tester.assert_true(False)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_3_assert_true(self):
        val = Tester.assert_true(None)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_1_assert_false(self):
        val = Tester.assert_false(False)
        self.assertEqual(True, val)

    def test_2_assert_false(self):
        val = Tester.assert_false(True)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_3_assert_false(self):
        val = Tester.assert_false(None)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_1_assert_in(self):
        val = Tester.assert_in(1, [1,2,3])
        self.assertEqual(True, val)

    def test_2_assert_in(self):
        val = Tester.assert_in('a', "abcde")
        self.assertEqual(True, val)

    def test_3_assert_in(self):
        val = Tester.assert_in('f', "abcde")
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_1_assert_not_in(self):
        val = Tester.assert_not_in(0, [1,2,3,4])
        self.assertEqual(True, val)

    def test_2_assert_not_in(self):
        val = Tester.assert_not_in('a', "abcde")
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_1_assert_greater(self):
        val = Tester.assert_greater(100, 1)
        self.assertEqual(True, val)

    def test_2_assert_greater(self):
        val = Tester.assert_greater(100, -1)
        self.assertEqual(True, val)

    def test_3_assert_greater(self):
        val = Tester.assert_greater(-1, 0)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_4_assert_greater(self):
        val = Tester.assert_greater(0, 0)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_1_assert_greater_equal(self):
        val = Tester.assert_greater_equal(0, 0)
        self.assertEqual(True, val)

    def test_2_assert_greater_equal(self):
        val = Tester.assert_greater_equal(1, 0)
        self.assertEqual(True, val)

    def test_3_assert_greater_equal(self):
        val = Tester.assert_greater_equal(-1, 0)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_1_assert_less(self):
        val = Tester.assert_less(-1, 0)
        self.assertEqual(True, val)

    def test_2_assert_less(self):
        val = Tester.assert_less(1, 100)
        self.assertEqual(True, val)

    def test_3_assert_less(self):
        val = Tester.assert_less(0, 0)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_4_assert_less(self):
        val = Tester.assert_less(100, 0)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

if __name__ == '__main__':
    unittest.main()
