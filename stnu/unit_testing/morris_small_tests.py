import unittest
from stnu.dc_checking import determine_dc, convert_to_normal_form
from classes.stnu import STNU


class TestMorris14(unittest.TestCase):

    def test_controllable(self):
        # Test example from Morris'14 paper
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')
        stnu.add_node('D')
        stnu.add_node('E')

        #stnu.set_ordinary_edge('B', 'E', -2)
        stnu.set_ordinary_edge('E', 'B', 4)
        stnu.set_ordinary_edge('B', 'D', 1)
        #stnu.set_ordinary_edge('D', 'B', 3)
        stnu.add_contingent_link('A', 'B', 0, 2)
        stnu.add_contingent_link('C', 'D', 0, 3)
        self.assertTrue(determine_dc(stnu, dispatchability=False))

    def test_edge_case(self):
        # Test example from Morris'14 paper
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')
        stnu.add_node('D')
        stnu.add_node('E')

        #stnu.set_ordinary_edge('B', 'E', -2)
        stnu.set_ordinary_edge('E', 'B', 4)
        stnu.set_ordinary_edge('B', 'D', 1)
        #stnu.set_ordinary_edge('D', 'B', 3)
        stnu.add_contingent_link('A', 'B', 0, 2)
        stnu.add_contingent_link('C', 'D', 0, 3)
        #self.assertFalse(determine_dc(stnu, dispatchability=False))
        determine_dc(stnu, dispatchability=True)

    def test_uncontrollable(self):
        # Test example from Morris'14 paper
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')
        stnu.add_node('D')
        stnu.add_node('E')

        stnu.set_ordinary_edge('B', 'E', -2)
        stnu.set_ordinary_edge('E', 'B', 4)
        stnu.set_ordinary_edge('B', 'D', 1)
        stnu.set_ordinary_edge('D', 'B', 3)
        stnu.add_contingent_link('A', 'B', 0, 2)
        stnu.add_contingent_link('C', 'D', 0, 3)
        self.assertFalse(determine_dc(stnu, dispatchability=False))

if __name__ == '__main__':
    unittest.main()
