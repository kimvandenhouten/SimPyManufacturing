import os
from classes.stnu import STNU

dir = 'stnu/java_comparison/xml_files'
file_name = 'input_slide118-output.stnu'

stnu = STNU.from_graphml(f'{dir}/{file_name}')
print(1)




