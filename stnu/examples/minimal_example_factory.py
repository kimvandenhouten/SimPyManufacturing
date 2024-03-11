from classes.stnu import STNU
from dc_checking import convert_to_normal_form, determine_dc

stnu = STNU()
stnu.add_node('A')
stnu.add_node('C')
stnu.add_node('D')
stnu.add_node('E')


stnu.set_edge('D', 'C', 0)  # resource constraint
stnu.set_edge('E', 'D', 8)  # max lag precedence constraint
stnu.set_edge('D', 'E', -5)  # min lag precedence constraint
stnu.add_contingent_link('A', 'C', 15, 20)

print(stnu)
print('\n')

determine_dc(stnu)

