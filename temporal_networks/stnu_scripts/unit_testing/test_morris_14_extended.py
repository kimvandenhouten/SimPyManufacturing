import unittest

from temporal_networks.dc_checking import determine_dc
from temporal_networks.stnu import STNU


class TestMorris14Extended(unittest.TestCase):
    def test_controllable(self):
        # Test example from slides Hunsberger, page 118
        stnu = STNU()
        a = stnu.add_node('A')
        b = stnu.add_node('B')
        c = stnu.add_node('C')

        stnu.set_ordinary_edge(b, c, 5)
        stnu.add_contingent_link(a, c, 2, 9)
        dc, network = determine_dc(stnu, dispatchability=True)
        self.assertTrue(dc)

    def test_uncontrollable(self):
        # Test example from Morris'14 paper
        stnu = STNU()
        a = stnu.add_node('A')
        b = stnu.add_node('B')
        c = stnu.add_node('C')
        d = stnu.add_node('D')
        e = stnu.add_node('E')

        stnu.set_ordinary_edge(b, e, -2)
        stnu.set_ordinary_edge(e, b, 4)
        stnu.set_ordinary_edge(b, d, 1)
        stnu.set_ordinary_edge(d, b, 3)
        stnu.add_contingent_link(a, b, 0, 2)
        stnu.add_contingent_link(c, d, 0, 3)
        dc, network = determine_dc(stnu, dispatchability=True)
        self.assertFalse(dc)

    def test_controllable_2(self):
        # Test example from paper Hunsberger'23, fig 7a
        stnu = STNU()
        a = stnu.add_node('A')
        c = stnu.add_node('C')
        w = stnu.add_node('W')
        x = stnu.add_node('X')
        y = stnu.add_node('Y')

        stnu.set_ordinary_edge(x, c, 3)
        stnu.set_ordinary_edge(x, y, -2)
        stnu.set_ordinary_edge(y, c, 1)
        stnu.set_ordinary_edge(c, w, -7)

        stnu.add_contingent_link(a, c, 1, 10)
        dc, network = determine_dc(stnu, dispatchability=True)
        self.assertTrue(dc)

    def test_edge_case(self):
        # Test example from Morris'14 paper adjusted
        stnu = STNU()
        a = stnu.add_node('A')
        b = stnu.add_node('B')
        c = stnu.add_node('C')
        d = stnu.add_node('D')
        e = stnu.add_node('E')

        stnu.set_ordinary_edge(e, b, 4)
        stnu.set_ordinary_edge(b, d, 1)
        stnu.add_contingent_link(a, b, 0, 2)
        stnu.add_contingent_link(c, d, 0, 3)
        dc, network = determine_dc(stnu, dispatchability=True)
        self.assertTrue(dc)




if __name__ == '__main__':
    unittest.main()
