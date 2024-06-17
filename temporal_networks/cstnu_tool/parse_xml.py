import os

from temporal_networks.stnu import STNU

dir = 'temporal_networks/cstnu_tool/xml_files'
files = [f for f in os.listdir(dir) if f.endswith('.stnu')]
for file_name in files:
    print(file_name)
    stnu = STNU.from_graphml(f'{dir}/{file_name}')
