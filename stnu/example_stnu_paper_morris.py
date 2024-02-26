from classes.stnu import STNU
from dc_checking import convert_to_normal_form, determine_dc

# Build simple example from slide 118
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
print(stnu)
print('\n')

determine_dc(stnu)

