import unittest
import json

from classes.classes import Factory, Product, Activity
from classes.distributions import NormalDistribution, ExponentialDistribution, PoissonDistribution


class TestFactory(unittest.TestCase):
    def test_object_mapping(self):
        fp = open('./resources-test/data.json', 'r')
        factory = Factory(**json.load(fp))
        self.assertEqual(factory.NAME, 'factory_1')
        self.assertEqual(len(factory.CAPACITY), 12)
        self.assertEqual(len(factory.PRODUCTS), 44)
        self.assertEqual(True, isinstance(factory.PRODUCTS[0], Product))
        self.assertEqual(True, isinstance(factory.PRODUCTS[0].ACTIVITIES[0], Activity))
        self.assertEqual(len(factory.PRODUCTS[0].TEMPORAL_RELATIONS.keys()), 13)
        fp.close()

    def test_distribution_mapping(self):
        fp = open('./resources-test/data_dist.json', 'r')
        factory = Factory(**json.load(fp))

        self.assertNotEqual(factory.PRODUCTS[0].ACTIVITIES[0].DISTRIBUTION.sample(), None)
        self.assertEqual(isinstance(factory.PRODUCTS[0].ACTIVITIES[0].DISTRIBUTION, NormalDistribution), True)

        self.assertNotEqual(factory.PRODUCTS[0].ACTIVITIES[1].DISTRIBUTION.sample(), None)
        self.assertEqual(isinstance(factory.PRODUCTS[0].ACTIVITIES[1].DISTRIBUTION, ExponentialDistribution), True)

        self.assertNotEqual(factory.PRODUCTS[0].ACTIVITIES[2].DISTRIBUTION.sample(), None)
        self.assertEqual(isinstance(factory.PRODUCTS[0].ACTIVITIES[2].DISTRIBUTION, PoissonDistribution), True)


if __name__ == '__main__':
    unittest.main()
