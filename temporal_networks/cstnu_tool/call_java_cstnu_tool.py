import enum
import os
import re
import subprocess

import general.logger
from general.config import Config

logger = general.logger.get_logger(__name__)


class DCAlgorithm(enum.Enum):
    FD_STNU_IMPROVED = enum.auto()
    FD_STNU = enum.auto()
    Morris2014Dispatchable = enum.auto()
    Morris2014 = enum.auto()
    RUL2018 = enum.auto()
    RUL2021 = enum.auto()


class RTEStrategy(enum.Enum):
    EARLY_EXECUTION_STRATEGY = enum.auto()
    FIRST_NODE_EARLY_EXECUTION_STRATEGY = enum.auto()
    FIRST_NODE_LATE_EXECUTION_STRATEGY = enum.auto()
    FIRST_NODE_MIDDLE_EXECUTION_STRATEGY = enum.auto()
    LATE_EXECUTION_STRATEGY = enum.auto()
    MIDDLE_EXECUTION_STRATEGY = enum.auto()
    RANDOM_EXECUTION_STRATEGY = enum.auto()


class CSTNUTool:
    jar_location = Config.get("tool", "cstnutool", "jar_location")
    if not jar_location:
        jar_location = "CSTNU-Tool.jar"

    logging_properties = Config.get("tool", "cstnutool", "logging_properties")

    if not os.path.exists(jar_location):
        raise Exception("Could not find CSTNUTool")

    @classmethod
    def _run_java(cls, java_class: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = ['java', '-cp', cls.jar_location]
        if cls.logging_properties:
            cmd.append(f'-Djava.util.logging.config.file={cls.logging_properties}')
        cmd.append(java_class)
        cmd += arguments

        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            raise Exception("Could not find java")

        if res.stderr:
            logger.error("ERROR")
            logger.error(res.stderr)

        logger.debug(res.stdout)
        return res

    @classmethod
    def run_rte(cls, instance_location, rte_decision_strategy: RTEStrategy = None,
                environment_strategy: RTEStrategy = None):
        java_class = 'it.univr.di.cstnu.algorithms.STNURTE'
        arguments = [
            instance_location,
        ]
        if rte_decision_strategy:
            arguments += ['-r', rte_decision_strategy.name]
        if environment_strategy:
            arguments += ['-e', environment_strategy.name]

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

    @classmethod
    def run_dc_alg(cls, instance_location, output_location=None,
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
        if is_dc:
            logger.debug('Network is DC')
        else:
            logger.debug('Network is not DC')

        return is_dc


def run_dc_algorithm(directory, file_name):
    instance_location = os.path.abspath(f"{directory}/{file_name}.stnu")
    if not os.path.exists(instance_location):
        logger.warning(f"warning: could not find {instance_location}")
        return False, None
    else:
        logger.debug(f"running CSTNUTool on {file_name}")

        output_location = instance_location.replace(".stnu", "-output.stnu")

        is_dc = CSTNUTool.run_dc_alg(instance_location, output_location)

    return is_dc, output_location


def run_rte_algorithm(instance_location):
    schedule = CSTNUTool.run_rte(instance_location, RTEStrategy.FIRST_NODE_EARLY_EXECUTION_STRATEGY,
                                 RTEStrategy.LATE_EXECUTION_STRATEGY)

    if schedule:
        logger.debug(f"parsed schedule: {schedule}")
    else:
        logger.debug("could not parse schedule")

    return schedule
