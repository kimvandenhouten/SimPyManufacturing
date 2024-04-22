import os
from classes.stnu import STNU
import classes.general
from stnu.algorithms.rte_star import RTEdata, Observation, rte_generate_decision, rte_update, rte_oracle
from stnu.java_comparison.call_cstnu_tool import CSTNUTool
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml

logger = classes.general.get_logger()

# Create your STNU here
stnu = STNU(origin_horizon=False)
a = stnu.add_node('A')
b = stnu.add_node('B')
c = stnu.add_node('C')
stnu.set_ordinary_edge(b, c, 5)
stnu.add_contingent_link(a, c, 2, 9)
stnu_to_xml(stnu, f"example_network", "stnu/java_comparison/xml_files")
expected_dc = True

# Here we run the CSTNU tool to check DC, and obtain ESTNU if DC=True
instance_location = os.path.abspath(f"stnu/java_comparison/xml_files/example_network.stnu")
if not os.path.exists(instance_location):
    raise FileNotFoundError(f"could not find {instance_location}")

logger.debug(f"running CSTNUTool")
output_location = instance_location.replace(".stnu", "-output.stnu")
CSTNUTool.run_dc_alg(instance_location, expected_dc, output_location)

# Here we read the ESTNU that is the output from the morris'14 dispatchable algorithm
estnu = STNU.from_graphml(f"stnu/java_comparison/xml_files/example_network-output.stnu")

# Here we start testing the RTE interaction
rte_data = RTEdata.from_estnu(estnu)

# First decision
rte_decision = rte_generate_decision(rte_data)
if rte_decision.fail:
    logger.debug(f'Decision is fail')
observation = Observation(rho=0, tau=[])
rte_data = rte_update(estnu, rte_data, rte_decision, observation)

# Second decision
rte_decision = rte_generate_decision(rte_data)
if rte_decision.fail:
    logger.debug(f'Decision is fail')
observation = Observation(rho=0, tau=[])
rte_data = rte_update(estnu, rte_data, rte_decision, observation)

# Third decision
rte_decision = rte_generate_decision(rte_data)
if rte_decision.fail:
    logger.debug(f'Decision is fail')
c = estnu.translation_dict_reversed["C"]
observation = rte_oracle(estnu, rte_data, rte_decision, seed=10)
#observation = Observation(rho=3, tau=[c])
rte_data = rte_update(estnu, rte_data, rte_decision, observation)

# Fourth decision
rte_decision = rte_generate_decision(rte_data)
if rte_decision.fail:
    logger.debug(f'Decision is fail')
observation = Observation(rho=3, tau=[])
rte_data = rte_update(estnu, rte_data, rte_decision, observation)
