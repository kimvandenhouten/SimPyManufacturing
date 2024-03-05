import unittest
from stnu.dc_checking import determine_dc
from classes.stnu import STNU


class TestMorris14(unittest.TestCase):
    def test_controllable(self):
        # Test example from slides Hunsberger, page 118
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')

        stnu.set_edge('B', 'C', 5)
        stnu.add_contingent_link('A', 'C', 2, 9)
        self.assertTrue(determine_dc(stnu))

    def test_controllable_2(self):
        # Test example from paper Hunsberger'23, fig 7a
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('C')
        stnu.add_node('W')
        stnu.add_node('X')
        stnu.add_node('Y')

        stnu.set_edge('X', 'C', 3)
        stnu.set_edge('X', 'Y', -2)
        stnu.set_edge('Y', 'C', 1)
        stnu.set_edge('C', 'W', -7)

        stnu.add_contingent_link('A', 'C', 1, 10)
        self.assertTrue(determine_dc(stnu))

    def test_uncontrollable(self):
        # Test example from Morris'14 paper
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')
        stnu.add_node('D')
        stnu.add_node('E')

        stnu.set_edge('B', 'E', -2)
        stnu.set_edge('E', 'B', 4)
        stnu.set_edge('B', 'D', 1)
        stnu.set_edge('D', 'B', 3)
        stnu.add_contingent_link('A', 'B', 0, 2)
        stnu.add_contingent_link('C', 'D', 0, 3)
        self.assertFalse(determine_dc(stnu))

    def test_uncontrollable2(self):
        # Test example Hunsberger slides, slide 140
        stnu = STNU()
        stnu.add_node('A1')
        stnu.add_node('A2')
        stnu.add_node('C1')
        stnu.add_node('C2')
        stnu.add_node('X')

        stnu.set_edge('C1', 'C2', -1)
        stnu.set_edge('C2', 'C1', 8)
        stnu.set_edge('C1', 'X', -7)
        stnu.set_edge('X', 'C1', 12)

        stnu.add_contingent_link('A1', 'C1', 1, 3)
        stnu.add_contingent_link('A2', 'C2', 1, 10)
        self.assertFalse(determine_dc(stnu))

if __name__ == '__main__':
    unittest.main()
