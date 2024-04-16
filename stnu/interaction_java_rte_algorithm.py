import enum
import os
import subprocess
from classes.stnu import STNU
import classes.general
logger = classes.general.get_logger()
from stnu.rte_star import RTEdata, Observation, rte_generate_decision, rte_update
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
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
    print(f"warning: could not find {instance_location}")

else:
    print(f"running CSTNUTool")

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
observation = Observation(rho=3, tau=[c])
rte_data = rte_update(estnu, rte_data, rte_decision, observation)

# Fourth decision
rte_decision = rte_generate_decision(rte_data)
if rte_decision.fail:
    logger.debug(f'Decision is fail')
observation = Observation(rho=3, tau=[])
rte_data = rte_update(estnu, rte_data, rte_decision, observation)
