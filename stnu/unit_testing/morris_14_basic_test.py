import unittest
from stnu.dc_checking import determine_dc, convert_to_normal_form
from classes.stnu import STNU


class TestMorris14Basic(unittest.TestCase):
    def test_controllable(self):
        # Test example from slides Hunsberger, page 118
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')
        stnu.set_ordinary_edge('B', 'C', 5)
        stnu.add_contingent_link('A', 'C', 2, 9)
        self.assertTrue(determine_dc(stnu, dispatchability=False))

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
        self.assertTrue(determine_dc(stnu, dispatchability=False))

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


    def test_normal_form_no_contingent_links(self):
        # Test example without contingent links
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.set_ordinary_edge('A', 'B', 10)

        nf_stnu = convert_to_normal_form(stnu)
        self.assertEqual(stnu, nf_stnu)

    def test_normal_form(self):
        # Test example without contingent links
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.set_ordinary_edge('A', 'B', 10)
        stnu.add_node('C')
        stnu.add_contingent_link('A', 'C', 2, 8)

        last_index = stnu.index
        nf_stnu = convert_to_normal_form(stnu)

        print(nf_stnu.nodes)
        print(nf_stnu.translation_dict)

        self.assertEqual(len(nf_stnu.contingent_links), 1)

        for (a, b, x, y) in nf_stnu.contingent_links:
            node_from_idx = last_index
            node_to_idx = stnu.translation_dict_reversed['C']
            self.assertEqual((a, b, x, y), (node_from_idx, node_to_idx, 0, y-x))

    def test_find_negative_nodes(self):
        # Test example without contingent links
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.set_ordinary_edge('A', 'B', -10)

        # there is also the origin and horizon index
        self.assertEqual(stnu.find_negative_nodes(), [False, False, False, True])

    def test_find_no_negative_nodes(self):
        # Test example without contingent links
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.set_ordinary_edge('A', 'B', 10)

        # there is also the origin and horizon index
        self.assertEqual(stnu.find_negative_nodes(), [False, False, False, False])

    def test_find_no_negative_nodes_2(self):
        # Test example without contingent links
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')

        # there is also the origin and horizon index
        self.assertEqual(stnu.find_negative_nodes(), [False, False, False, False])


if __name__ == '__main__':
    unittest.main()
