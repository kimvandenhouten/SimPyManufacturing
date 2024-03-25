import unittest
from stnu.dc_checking import determine_dc, convert_to_normal_form
from classes.stnu import STNU


class TestMorris14Extended(unittest.TestCase):
    def test_controllable(self):
        # Test example from slides Hunsberger, page 118
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')

        stnu.set_ordinary_edge('B', 'C', 5)
        stnu.add_contingent_link('A', 'C', 2, 9)
        dc, network = determine_dc(stnu, dispatchability=True)
        self.assertTrue(dc)

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
        dc, network = determine_dc(stnu, dispatchability=True)
        self.assertFalse(dc)

    def test_controllable_2(self):
        # Test example from paper Hunsberger'23, fig 7a
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('C')
        stnu.add_node('W')
        stnu.add_node('X')
        stnu.add_node('Y')

        stnu.set_ordinary_edge('X', 'C', 3)
        stnu.set_ordinary_edge('X', 'Y', -2)
        stnu.set_ordinary_edge('Y', 'C', 1)
        stnu.set_ordinary_edge('C', 'W', -7)

        stnu.add_contingent_link('A', 'C', 1, 10)
        dc, network = determine_dc(stnu, dispatchability=True)
        self.assertTrue(dc)

    def test_edge_case(self):
        # Test example from Morris'14 paper adjusted
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')
        stnu.add_node('D')
        stnu.add_node('E')

        stnu.set_ordinary_edge('E', 'B', 4)
        stnu.set_ordinary_edge('B', 'D', 1)
        stnu.add_contingent_link('A', 'B', 0, 2)
        stnu.add_contingent_link('C', 'D', 0, 3)
        dc, network = determine_dc(stnu, dispatchability=True)
        self.assertTrue(dc)




if __name__ == '__main__':
    unittest.main()
