import re
import subprocess
import pandas as pd

# Define the script to run and the number of times to run it
script_to_run = "simulators/simulator7/example_cp_output_to_simulator_7_stochastic.py"
num_runs = 10

df = pd.DataFrame(columns=["instance", "makespan", "lateness", "unfinished_products", "clashes"])

# Create a loop to run the script multiple times
for i in range(num_runs):
    try:
        # Run the script and capture the output
        result = subprocess.run(["python", script_to_run], stdout=subprocess.PIPE, text=True, check=True)
        input_text = result.stdout

        instance_name_pattern = r"Run simulation for a scenario for instance (.+)"
        makespan_pattern = r"the makespan is ([\d.]+)"
        lateness_pattern = r"the lateness is ([\d.]+)"
        unfinished_products_pattern = r"The number of unfinished products (\d+)"
        clashes_pattern = r"The number of clashes \(i.e\. activities that could not be processed\) is (\d+)"

        # Use re.findall to find and extract all occurrences of the values
        instance_name_match = re.findall(instance_name_pattern, input_text)
        makespan_matches = re.findall(makespan_pattern, input_text)
        lateness_matches = re.findall(lateness_pattern, input_text)
        unfinished_products_matches = re.findall(unfinished_products_pattern, input_text)
        clashes_matches = re.findall(clashes_pattern, input_text)

        # Print the extracted values
        # print(instance_name_match)
        # print("Makespan values:", makespan_matches)
        # print("Lateness values:", lateness_matches)
        # print("Unfinished Products values:", unfinished_products_matches)
        # print("Clashes values:", clashes_matches)
        run_df = pd.DataFrame(
            {"instance": instance_name_match, "makespan": makespan_matches, "lateness": lateness_matches,
             "unfinished_products": unfinished_products_matches, "clashes": clashes_matches})

        df = pd.concat([df, run_df], axis=0, ignore_index=True)

    except subprocess.CalledProcessError as e:
        print(f"Error running the script: {e}")

print(df)
