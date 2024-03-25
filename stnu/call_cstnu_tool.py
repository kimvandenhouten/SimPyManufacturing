import subprocess

JAR_LOCATION = "/home/leon/Projects/CstnuTool-4.12/CSTNU-Tool-4.12.jar"
INSTANCE_LOCATION = "/home/leon/Projects/CstnuTool-4.12/Instances/AI4B.io/example_morris14_paper.stnu"

cmd = [
    'java',
    '-cp',
    JAR_LOCATION,
    'it.univr.di.cstnu.algorithms.STNU',
    INSTANCE_LOCATION,
]

res = subprocess.run(cmd, capture_output=True, text=True)
print(res.stdout)
