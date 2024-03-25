import unittest
from stnu.dc_checking import apply_reduction_rule
from classes.stnu import STNU


class TestMorris14ReductionRules(unittest.TestCase):
    #def test_reduction_rule(self):

    def test_no_case(self):
        # Test example from slides Hunsberger, page 118
        stnu = STNU()
        stnu.add_node('Q')
        stnu.add_node('S')
        stnu.add_node('T')

        stnu.set_ordinary_edge('Q', 'S', 3)
        stnu.set_ordinary_edge('S', 'T', 4)

        source = stnu.translation_dict_reversed['T']
        u = stnu.translation_dict_reversed['S']
        v = stnu.translation_dict_reversed['Q']

        type_u_source = STNU.ORDINARY_LABEL
        type_v_u = STNU.ORDINARY_LABEL
        weight_u_source = 4
        weight_v_u = 3
        label_u_source = None
        label_v_u = None

        new_distance = 7

        new_distance, v, new_type, new_label = apply_reduction_rule(stnu, source, u, v, type_u_source, type_v_u, weight_u_source, weight_v_u, label_u_source, label_v_u, new_distance)

        self.assertEqual(new_type, STNU.ORDINARY_LABEL)

    def upper_case(self):
        # Test example from slides Hunsberger, page 118
        stnu = STNU()
        stnu.add_node('Q')
        stnu.add_node('C')
        stnu.add_node('A')

        # To do, set contingent edge
        stnu.set_ordinary_edge('Q', 'C', 3)
        stnu.set_ordinary_edge('S', 'T', 4)

        source = stnu.translation_dict_reversed['T']
        u = stnu.translation_dict_reversed['S']
        v = stnu.translation_dict_reversed['Q']

        type_u_source = STNU.ORDINARY_LABEL
        type_v_u = STNU.ORDINARY_LABEL
        weight_u_source = 4
        weight_v_u = 3
        label_u_source = None
        label_v_u = None

        new_distance = 7

        new_distance, v, new_type, new_label = apply_reduction_rule(stnu, source, u, v, type_u_source, type_v_u, weight_u_source, weight_v_u, label_u_source, label_v_u, new_distance)

        self.assertEqual(new_type, STNU.ORDINARY_LABEL)

if __name__ == '__main__':
    unittest.main()
