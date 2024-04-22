import os
from classes.stnu import STNU
import classes.general
from stnu.algorithms.rte_star import rte_star
from stnu.java_comparison.call_cstnu_tool import CSTNUTool
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import numpy as np

logger = classes.general.get_logger()

# Create your STNU here
stnu = STNU(origin_horizon=False)
a = stnu.add_node('A')
b = stnu.add_node('B')
c = stnu.add_node('C')
stnu.set_ordinary_edge(b, c, 5)
stnu.add_contingent_link(a, c, 2, 9)
directory = "stnu/java_comparison/xml_files"
name_graph = "example_network"
stnu_to_xml(stnu, name_graph, directory)
expected_dc = True

# Here we run the CSTNU tool to check DC, and obtain ESTNU if DC=True
instance_location = os.path.abspath(f"{directory}/{name_graph}.stnu")

if not os.path.exists(instance_location):
    raise FileNotFoundError("could not find {instance_location}")

logger.debug(f"running CSTNUTool")
output_location = instance_location.replace(".stnu", "-output.stnu")
CSTNUTool.run_dc_alg(instance_location, expected_dc, output_location)

# Here we read the ESTNU that is the output from the morris'14 dispatchable algorithm
estnu = STNU.from_graphml(output_location)

# Here we start testing the RTE interaction
sample = {}
# TODO: for all contingent timepoints sample the duration
for (A, C) in estnu.contingent_links:
    duration_sample = np.random.randint(estnu.contingent_links[(A, C)]["lc_value"], estnu.contingent_links[(A, C)]["uc_value"])
    sample[C] = duration_sample
logger.debug(f'Sample that will be given to RTE_star: {sample}')
rte_data = rte_star(estnu, oracle="sample", sample=sample)
#rte_data = rte_star(estnu, oracle="standard")
logger.debug(f'the final schedule is {rte_data.f}')
logger.debug(f'the makespan is {max(rte_data.f.values())}')
logger.debug(f'the sampled weights are {rte_data.sampled_weights}')
