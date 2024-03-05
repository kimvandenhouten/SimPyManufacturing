import unittest
from stnu.unit_testing.mymodule import add


class TestAdd(unittest.TestCase):
    def test_add_integers(self):
        self.assertEqual(add(1, 2), 3)

    def test_add_negative(self):
        self.assertEqual(add(-1, -2), -3)

    def test_add_floats(self):
        self.assertAlmostEqual(add(0.1, 0.2), 0.3, places=2)


if __name__ == '__main__':
    unittest.main()