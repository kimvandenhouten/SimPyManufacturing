from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
from classes.stnu import STNU
from stnu.dc_checking import convert_to_normal_form, determine_dc

# Example Hunsberger slide 118 (controllable)
name = "slide118"
stnu = STNU()
stnu.add_node('A')
stnu.add_node('B')
stnu.add_node('C')
stnu.set_ordinary_edge('B', 'C', 5)
stnu.add_contingent_link('A', 'C', 2, 9)
stnu_to_xml(stnu, f"input_{name}", "stnu/java_comparison/xml_files")
dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "stnu/java_comparison/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "stnu/java_comparison/xml_files")


# Test example from paper Hunsberger'23, fig 7a (controllable)
name = "hunsberger23"
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
stnu_to_xml(stnu, f"input_{name}", "stnu/java_comparison/xml_files")
dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "stnu/java_comparison/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "stnu/java_comparison/xml_files")

# Test example from Morris'14 paper
name = "morris14"
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
stnu_to_xml(stnu, f"input_{name}", "stnu/java_comparison/xml_files")
dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "stnu/java_comparison/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "stnu/java_comparison/xml_files")

# Test minimal example factory
name = "minimal_example_factory"
stnu = STNU()
stnu.add_node('A')
stnu.add_node('C')
stnu.add_node('D')
stnu.add_node('E')

stnu.set_ordinary_edge('D', 'C', 0)  # resource constraint
stnu.set_ordinary_edge('E', 'D', 8)  # max lag precedence constraint
stnu.set_ordinary_edge('D', 'E', -5)  # min lag precedence constraint
stnu.add_contingent_link('A', 'C', 15, 20)
stnu_to_xml(stnu, f"input_{name}", "stnu/java_comparison/xml_files")

dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "stnu/java_comparison/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "stnu/java_comparison/xml_files")

# Test minimal example factory
name = "minimized_example_factory"
stnu = STNU()
stnu.add_node('A')
stnu.add_node('C')
stnu.add_node('D')
stnu.add_node('E')


stnu.set_ordinary_edge('D', 'C', 0)  # resource constraint
stnu.set_ordinary_edge('E', 'D', 8)  # max lag precedence constraint
stnu.set_ordinary_edge('D', 'E', -5)  # min lag precedence constraint
stnu.add_contingent_link('A', 'C', 0, 20)
stnu_to_xml(stnu, f"input_{name}", "stnu/java_comparison/xml_files")
dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "stnu/java_comparison/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "stnu/java_comparison/xml_files")

