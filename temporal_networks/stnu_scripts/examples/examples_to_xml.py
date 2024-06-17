from temporal_networks.cstnu_tool.stnu_to_xml_function import stnu_to_xml
from temporal_networks.dc_checking import convert_to_normal_form, determine_dc
from temporal_networks.stnu import STNU

# Example Hunsberger slide 118 (controllable)
name = "slide118"
stnu = STNU()
a = stnu.add_node('A')
b = stnu.add_node('B')
c = stnu.add_node('C')
stnu.set_ordinary_edge(b, c, 5)
stnu.add_contingent_link(a, c, 2, 9)
stnu_to_xml(stnu, f"input_{name}", "temporal_networks/cstnu_tool/xml_files")
dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "temporal_networks/cstnu_tool/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "temporal_networks/cstnu_tool/xml_files")


# Test example from paper Hunsberger'23, fig 7a (controllable)
name = "hunsberger23"
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
stnu_to_xml(stnu, f"input_{name}", "temporal_networks/cstnu_tool/xml_files")
dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "temporal_networks/cstnu_tool/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "temporal_networks/cstnu_tool/xml_files")

# Test example from Morris'14 paper
name = "morris14"
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
stnu_to_xml(stnu, f"input_{name}", "temporal_networks/cstnu_tool/xml_files")
dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "temporal_networks/cstnu_tool/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "temporal_networks/cstnu_tool/xml_files")

# Test minimal example factory
name = "minimal_example_factory"
stnu = STNU()
a = stnu.add_node('A')
c = stnu.add_node('C')
d = stnu.add_node('D')
e = stnu.add_node('E')

stnu.set_ordinary_edge(d, c, 0)  # resource constraint
stnu.set_ordinary_edge(e, d, 8)  # max lag precedence constraint
stnu.set_ordinary_edge(d, e, -5)  # min lag precedence constraint
stnu.add_contingent_link(a, c, 15, 20)
stnu_to_xml(stnu, f"input_{name}", "temporal_networks/cstnu_tool/xml_files")

dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "temporal_networks/cstnu_tool/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "temporal_networks/cstnu_tool/xml_files")

# Test minimal example factory
name = "minimized_example_factory"
stnu = STNU()
a = stnu.add_node('A')
c = stnu.add_node('C')
d = stnu.add_node('D')
e = stnu.add_node('E')


stnu.set_ordinary_edge(d, c, 0)  # resource constraint
stnu.set_ordinary_edge(e, d, 8)  # max lag precedence constraint
stnu.set_ordinary_edge(d, e, -5)  # min lag precedence constraint
stnu.add_contingent_link(a, c, 0, 20)
stnu_to_xml(stnu, f"input_{name}", "temporal_networks/cstnu_tool/xml_files")
dc, estnu = determine_dc(stnu, dispatchability=True)
if dc:
    stnu_to_xml(estnu, f"output_estnu_python_{name}", "temporal_networks/cstnu_tool/xml_files")

# Example Hunsberger slide 118 (controllable) in normal form
stnu = convert_to_normal_form(stnu)
stnu_to_xml(stnu, f"input_normal_form_{name}", "temporal_networks/cstnu_tool/xml_files")

