import enum
import os
import subprocess

import pandas as pd

from classes.stnu import STNU
import classes.general
logger = classes.general.get_logger()
from stnu.algorithms.rte_star import rte_star
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import numpy as np

class DCAlgorithm(enum.Enum):
    FD_STNU_IMPROVED = enum.auto()
    FD_STNU = enum.auto()
    Morris2014Dispatchable = enum.auto()
    Morris2014 = enum.auto()
    RUL2018 = enum.auto()
    RUL2021 = enum.auto()


class CSTNUTool:
    JAR_LOCATION = None

    if os.path.exists("/Users/kimvandenhouten"):
        JAR_LOCATION = "/Users/kimvandenhouten/Documents/PhD/Repositories/CstnuTool-4.12-ai4b.io/CSTNU-Tool-4.12-ai4b.io.jar"
    elif os.path.exists("/home/leon"):
        JAR_LOCATION = "/home/leon/Projects/CstnuTool-4.12-ai4b.io/CSTNU-Tool-4.12-ai4b.io.jar"

    if not JAR_LOCATION or not os.path.exists(JAR_LOCATION):
        raise Exception("Could not find CSTNUTool")

    @classmethod
    def _run_java(cls, java_class: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [
            'java', '-cp', cls.JAR_LOCATION,
            java_class,
        ]
        cmd += arguments

        res = subprocess.run(cmd, capture_output=True, text=True)

        if res.stderr:
            print("ERROR")
            print(res.stderr)

        print(res.stdout)
        return res

    @classmethod
    def run_dc_alg(cls, instance_location, expected_dc, output_location=None,
                   alg: DCAlgorithm = DCAlgorithm.Morris2014Dispatchable):
        java_class = 'it.univr.di.cstnu.algorithms.STNU'
        arguments = [
            instance_location,
            '-a', alg.name,
        ]
        if output_location:
            arguments += ['-o', output_location]

        res = cls._run_java(java_class, arguments)

        is_dc = "The given STNU is dynamic controllable!" in res.stdout
        if expected_dc and is_dc:
            print('Network is DC, as expected')
        elif not expected_dc and not is_dc:
            print('Network is not DC, as expected')
        else:
            print(f'WARNING: Network was unexpectedly found {"" if is_dc else "not "} to be DC')

# Read your STNU input graph here
instance_location = os.path.abspath(f"stnu/java_comparison/xml_files/input_production_plan_10_1.stnu")

# Now run Morris'14Dispatchable
expected_dc = True
if not os.path.exists(instance_location):
    print(f"warning: could not find {instance_location}")

else:
    print(f"running CSTNUTool")

    output_location = instance_location.replace(".stnu", "-output.stnu")

    CSTNUTool.run_dc_alg(instance_location, expected_dc, output_location)

# Here we read the ESTNU that is the output from the morris'14 dispatchable algorithm
estnu = STNU.from_graphml(f"stnu/java_comparison/xml_files/input_production_plan_10_1-output.stnu")

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
data = []
for tp in rte_data.f:
    data.append({"node_idx": tp,
                 "assignment": rte_data.f[tp],
                 "description": estnu.translation_dict[tp]})
data_df = pd.DataFrame(data)
makespan = max(rte_data.f.values())
logger.debug(f'the makespan is {makespan}')
data_df.to_csv(f"stnu/examples/schedules/schedule_production_plan_10_1_makespan={makespan}.csv")

logger.debug(f'the sampled weights are {rte_data.sampled_weights}')

# Check if the sampled weights match the given sample
assert rte_data.sampled_weights == sample

data = []
for cont_tp in rte_data.sampled_weights:
    data.append({"node_idx": cont_tp,
                 "weight": rte_data.sampled_weights[cont_tp],
                 "description": estnu.translation_dict[cont_tp]})
data_df = pd.DataFrame(data)
data_df.to_csv(f"stnu/examples/schedules/sampled_weights_production_plan_10_1_makespan={makespan}.csv")

# FIXME: this is all very ugly and inefficient
durations = []
for product in my_productionplan.products:
    for activity in product.activities:
        key = f'{product.product_index}_{activity.id}_finish'
        index = keys.index(key)
        weight = weights[index]
        durations.append(weight)

# Solve under perfect information
rcpsp = RCPSP_CP(my_productionplan)
print(len(rcpsp.durations))
# TODO: set durations obtained from
_, _, cp_output = rcpsp.solve(durations,1800, 1, 0)
makespan_cp_output = max(cp_output["end"].tolist())
logger.info(f'makespan under perfect information is {makespan_cp_output}, makespan obtained with STNU is 1408, regret is {1408-makespan_cp_output}')


