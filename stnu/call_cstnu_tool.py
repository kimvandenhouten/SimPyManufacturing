import subprocess

#JAR_LOCATION = "/home/leon/Projects/CstnuTool-4.12/CSTNU-Tool-4.12.jar"
#INSTANCE_LOCATION = "/home/leon/Projects/CstnuTool-4.12/Instances/AI4B.io/example_morris14_paper.stnu"

for (file_name, dc) in [("output_hunsberger23.stnu", True), ("output_morris14.stnu", False), ("output_slide118.stnu", True)]:
    JAR_LOCATION = "/Users/kimvandenhouten/Documents/PhD/Repositories/CstnuTool-4.12/CSTNU-Tool-4.12.jar"
    INSTANCE_LOCATION = f"/Users/kimvandenhouten/Documents/PhD/Repositories/CstnuTool-4.12/Instances/AI4b.io/{file_name}"
    # FIXME: can't we read directly from this repo ?
    #INSTANCE_LOCATION = f"Users/kimvandenhouten/SimPyManufacturing/stnu/java_comparison/xml_files/{file_name}"

    cmd = [
        'java',
        '-cp',
        JAR_LOCATION,
        'it.univr.di.cstnu.algorithms.STNU',
        INSTANCE_LOCATION,
    ]
    if dc:
        print(f'Network should be DC')
    else:
        print(f'Network should not be DC')
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
