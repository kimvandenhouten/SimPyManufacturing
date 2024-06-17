import enum
import os
import re
import subprocess

import general.logger

logger = general.logger.get_logger(__name__)


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
            logger.error("ERROR")
            logger.error(res.stderr)

        logger.debug(res.stdout)
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
            logger.debug('Network is DC, as expected')
        elif not expected_dc and not is_dc:
            logger.debug('Network is not DC, as expected')
        else:
            logger.warning(f'WARNING: Network was unexpectedly found {"" if is_dc else "not "} to be DC')

    @classmethod
    def run_rte(cls, instance_location):
        java_class = 'it.univr.di.cstnu.algorithms.STNURTE'
        arguments = [
            instance_location,
        ]

        res = cls._run_java(java_class, arguments)
        match = re.search(r'Final schedule: \[(.*)]', res.stdout)
        if match:
            schedule = {}
            for s in match[1].split(', '):
                var, val = s.split('=>')
                schedule[var[1:-1]] = int(val)
            return schedule
        else:
            return None


def main():
    file_list = [
        ("example_rcpsp_max_stnu.stnu", True)
    ]

    for (file_name, dc) in file_list:
        instance_location = os.path.abspath(f"temporal_networks/cstnu_tool/xml_files/{file_name}")
        if not os.path.exists(instance_location):
            logger.warning(f"warning: could not find {instance_location}")
            continue
        logger.debug(f"running CSTNUTool on {file_name}")

        output_location = instance_location.replace(".stnu", "-output.stnu")

        CSTNUTool.run_dc_alg(instance_location, dc, output_location)
        schedule = CSTNUTool.run_rte(instance_location)
        if schedule:
            logger.debug(f"parsed schedule: {schedule}")
        else:
            logger.debug("could not parse schedule")


if __name__ == "__main__":
    main()
