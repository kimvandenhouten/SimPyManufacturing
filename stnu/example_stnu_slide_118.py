from classes.stnu import STNU
from dc_checking import convert_to_normal_form, determine_dc

# Build simple example from slide 118
stnu = STNU()
stnu.add_node('A')
stnu.add_node('B')
stnu.add_node('C')

stnu.set_edge('B', 'C', 5)
stnu.add_contingent_link('A', 'C', 2, 9)
print(stnu)
print('\n')

determine_dc(stnu)

