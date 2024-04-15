import os
from classes.stnu import STNU

dir = 'stnu/java_comparison/xml_files'
files = [f for f in os.listdir(dir) if f.endswith('.stnu')]
for file_name in files:
    print(file_name)
    stnu = STNU.from_graphml(f'{dir}/{file_name}')

