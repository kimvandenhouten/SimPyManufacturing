from classes.stnu import STNU
from dc_checking import convert_to_normal_form

# Build simple example from slide 118
stnu = STNU()
stnu.add_node('A')
stnu.add_node('B')
stnu.add_node('C')
stnu.set_edge('B', 'C', 5)
stnu.add_contingent_link('A', 'C', 2, 9)
print(stnu)

print(f'\nCONVERT TO NORMAL FORM')
# Print STNU object, note that origin and horizon are added
normal_form_stnu = convert_to_normal_form(stnu)
print(normal_form_stnu)

