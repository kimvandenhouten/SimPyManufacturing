import unittest
import json

from classes.classes import Factory, Product, Activity


class TestFactory(unittest.TestCase):
    def test_object_mapping(self):
        fp = open('tests/resources-test/data.json','r')
        factory = Factory(**json.load(fp)["FACTORIES"][0])
        self.assertEqual(factory.NAME, 'factory_1')
        self.assertEqual(len(factory.CAPACITY), 12)
        self.assertEqual(len(factory.PRODUCTS), 44)
        self.assertEqual(True,isinstance(factory.PRODUCTS[0],Product))
        self.assertEqual(True, isinstance(factory.PRODUCTS[0].ACTIVITIES[0],Activity))
        fp.close()


if __name__ == '__main__':
    unittest.main()
