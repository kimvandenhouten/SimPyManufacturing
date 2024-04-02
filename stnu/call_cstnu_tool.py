import os
import subprocess

JAR_LOCATION = None

if os.path.exists("/Users/kimvandenhouten"):
    JAR_LOCATION = "/Users/kimvandenhouten/Documents/PhD/Repositories/CstnuTool-4.12/CSTNU-Tool-4.12.jar"
elif os.path.exists("/home/leon"):
    JAR_LOCATION = "/home/leon/Projects/CstnuTool-4.12-ai4b.io/CSTNU-Tool-4.12-ai4b.io.jar"

if not JAR_LOCATION or not os.path.exists(JAR_LOCATION):
    raise Exception("Could not find CSTNUTool")

FILE_LIST = [
    ("input_hunsberger23.stnu", True),
    ("input_morris14.stnu", False),
    ("input_slide118.stnu", True)
]

for (file_name, dc) in FILE_LIST:
    INSTANCE_LOCATION = os.path.abspath(f"stnu/java_comparison/xml_files/{file_name}")
    if not os.path.exists(INSTANCE_LOCATION):
        print(f"warning: could not find {INSTANCE_LOCATION}")
        continue
    print(f"running CSTNUTool on {file_name}")

    OUTPUT_LOCATION = INSTANCE_LOCATION.replace(".stnu", "-output.stnu")

    cmd = [
        'java', '-cp', JAR_LOCATION,
        'it.univr.di.cstnu.algorithms.STNU',
        INSTANCE_LOCATION,
        '-a', 'Morris2014',
        '-o', OUTPUT_LOCATION,
    ]
    if dc:
        print(f'Network should be DC')
    else:
        print(f'Network should not be DC')

    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.stderr:
        print("ERROR")
        print(res.stderr)

    print(res.stdout)
