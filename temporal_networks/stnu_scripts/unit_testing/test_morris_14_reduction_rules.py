import unittest

from temporal_networks.dc_checking import apply_reduction_rule
from temporal_networks.stnu import STNU


class TestMorris14ReductionRules(unittest.TestCase):
    #def test_reduction_rule(self):

    def test_no_case(self):
        # Test no case (slide 131)
        stnu = STNU()
        q = stnu.add_node('Q')
        s = stnu.add_node('S')
        t = stnu.add_node('T')

        stnu.set_ordinary_edge(q, s, 3)
        stnu.set_ordinary_edge(s, t, 4)

        source = stnu.translation_dict_reversed['T']
        u = stnu.translation_dict_reversed['S']
        v = stnu.translation_dict_reversed['Q']

        type_u_source = STNU.ORDINARY_LABEL
        type_v_u = STNU.ORDINARY_LABEL
        weight_u_source = 3
        weight_v_u = 4
        label_u_source = None
        label_v_u = None

        new_distance = 7

        new_distance, v, new_type, new_label = apply_reduction_rule(stnu, source, u, v, type_u_source, type_v_u, weight_u_source, weight_v_u, label_u_source, label_v_u, new_distance)

        self.assertEqual(new_type, STNU.ORDINARY_LABEL)
        self.assertEqual(new_distance, 7)

    def test_upper_case(self):
        # Test upper case (slide 132)
        stnu = STNU()
        q = stnu.add_node('Q')
        c = stnu.add_node('C')
        a = stnu.add_node('A')

        # To do, set contingent edge
        stnu.set_ordinary_edge(q, c, 3)
        stnu.set_labeled_edge(c, a, -10, 'C', STNU.UC_LABEL)

        source = stnu.translation_dict_reversed['A']
        u = stnu.translation_dict_reversed['C']
        v = stnu.translation_dict_reversed['Q']

        type_u_source = STNU.UC_LABEL
        type_v_u = STNU.ORDINARY_LABEL
        weight_u_source = -10
        weight_v_u = 3
        label_u_source = 'C'
        label_v_u = None

        new_distance = -7
        new_distance, v, new_type, new_label = apply_reduction_rule(stnu, source, u, v, type_u_source, type_v_u, weight_u_source, weight_v_u, label_u_source, label_v_u, new_distance)

        self.assertEqual(new_type, STNU.UC_LABEL)
        self.assertEqual(new_distance, -7)

    def test_lower_case(self):
        # Test lower case (slide 133)
        stnu = STNU()
        a = stnu.add_node('A')
        c = stnu.add_node('C')
        x = stnu.add_node('X')

        # To do, set contingent edge
        stnu.set_ordinary_edge(c, x, -5)
        stnu.set_labeled_edge(a, c, 3, 'C', STNU.LC_LABEL)

        source = stnu.translation_dict_reversed['X']
        u = stnu.translation_dict_reversed['C']
        v = stnu.translation_dict_reversed['A']

        type_u_source = STNU.ORDINARY_LABEL
        type_v_u = STNU.LC_LABEL
        weight_u_source = -5
        weight_v_u = 3
        label_u_source = None
        label_v_u = 'C'

        new_distance = -2
        new_distance, v, new_type, new_label = apply_reduction_rule(stnu, source, u, v, type_u_source, type_v_u,
                                                                    weight_u_source, weight_v_u, label_u_source,
                                                                    label_v_u, new_distance)

        self.assertEqual(new_type, STNU.ORDINARY_LABEL)
        self.assertEqual(new_distance, -2)

    def test_cross_case(self):
        # Test cross case (slide 134)
        stnu = STNU()
        a = stnu.add_node('A')
        c = stnu.add_node('C')
        a_d = stnu.add_node('A_d')

        # To do, set contingent edge
        stnu.set_labeled_edge(c, a_d, -8, 'K', STNU.UC_LABEL)
        stnu.set_labeled_edge(a, c, 3, 'C', STNU.LC_LABEL)

        source = stnu.translation_dict_reversed['A']
        u = stnu.translation_dict_reversed['C']
        v = stnu.translation_dict_reversed['A_d']

        type_u_source = STNU.UC_LABEL
        type_v_u = STNU.LC_LABEL
        weight_u_source = -8
        weight_v_u = 3
        label_u_source = 'D'
        label_v_u = 'C'

        new_distance = -5
        new_distance, v, new_type, new_label = apply_reduction_rule(stnu, source, u, v, type_u_source, type_v_u, weight_u_source, weight_v_u, label_u_source, label_v_u, new_distance)

        self.assertEqual(new_type, STNU.UC_LABEL)
        self.assertEqual(new_distance, -5)

if __name__ == '__main__':
    unittest.main()
