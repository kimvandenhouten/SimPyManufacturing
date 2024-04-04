import unittest
from stnu.dc_checking import determine_dc, convert_to_normal_form
from classes.stnu import STNU


class TestMorris14Basic(unittest.TestCase):
    def test_tp_types(self):
        # Test example from slides Hunsberger, page 118
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')
        stnu.set_ordinary_edge('B', 'C', 5)
        stnu.add_contingent_link('A', 'C', 2, 9)
        executable_tps = stnu.get_executable_time_points()
        contingent_tps = stnu.get_contingent_time_points()

        self.assertEqual(executable_tps, [0, 1, 2, 3])

    def test_tp_types_nf(self):
        # Test example from slides Hunsberger, page 118
        stnu = STNU()
        stnu.add_node('A')
        stnu.add_node('B')
        stnu.add_node('C')
        stnu.set_ordinary_edge('B', 'C', 5)
        stnu.add_contingent_link('A', 'C', 2, 9)
        stnu = convert_to_normal_form(stnu)
        executable_tps = stnu.get_executable_time_points()
        contingent_tps = stnu.get_contingent_time_points()
        self.assertEqual(executable_tps, [0, 1, 2, 3, 5])

