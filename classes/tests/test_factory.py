import unittest
import json

from classes.classes import Factory, Product, Activity
from classes.distributions import NormalDistribution, ExponentialDistribution, PoissonDistribution, \
    LogNormalDistribution


class TestFactory(unittest.TestCase):
    def test_object_mapping(self):
        fp = open('./resources-test/data.json', 'r')
        factory = Factory(**json.load(fp))
        self.assertEqual(factory.name, 'factory_1')
        self.assertEqual(len(factory.capacity), 12)
        self.assertEqual(len(factory.products), 44)
        self.assertEqual(True, isinstance(factory.products[0], Product))
        self.assertEqual(True, isinstance(factory.products[0].activities[0], Activity))
        self.assertEqual(len(factory.products[0].temporal_relations.keys()), 13)
        fp.close()

    def test_distribution_mapping(self):
        fp = open('./resources-test/data_dist.json', 'r')
        factory = Factory(**json.load(fp))

        self.assertNotEqual(factory.products[0].activities[0].distribution.sample(), None)
        self.assertEqual(isinstance(factory.products[0].activities[0].distribution, NormalDistribution), True)

        self.assertNotEqual(factory.products[0].activities[1].distribution.sample(), None)
        self.assertEqual(isinstance(factory.products[0].activities[1].distribution, ExponentialDistribution), True)

        self.assertNotEqual(factory.products[0].activities[2].distribution.sample(), None)
        self.assertEqual(isinstance(factory.products[0].activities[2].distribution, PoissonDistribution), True)

        self.assertNotEqual(factory.products[0].activities[3].distribution.sample(), None)
        self.assertEqual(isinstance(factory.products[0].activities[3].distribution, LogNormalDistribution), True)


if __name__ == '__main__':
    unittest.main()
