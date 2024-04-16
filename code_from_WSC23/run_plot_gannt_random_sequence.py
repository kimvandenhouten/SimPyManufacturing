import altair_viewer
import pandas as pd
import altair as alt

"""
This script can be used to make a gannt chart from the resource usage table
for a random solution to a problem instance
"""
modus = "save"
simulator_name = "SimPyClaimOneByOneWithDelay"

for factory_name in ["factory_4"]:
    for instance in ['40_1']:
        for seed in range(1, 2):
            file_name = f'simulator={simulator_name}_instance_{instance}_{factory_name}_seed={seed}'
            schedule = pd.read_csv(f'results/resource_usage/{file_name}.csv',  index_col=0)
            print(schedule)
            print(list(schedule))
            schedule["Machine_id"] = [f'_id={i}' for i in schedule["Machine_id"].tolist()]
            schedule['Machine'] = schedule['Resource'] + schedule['Machine_id']

            width_formula = max(schedule["Finish"])
            # Plot schedule for claim times
            chart1 = alt.Chart(schedule).mark_bar().encode(
                x='Retrieve moment',
                x2='Finish',
                y='Machine',
                color=alt.Color('Product:N',
                                legend=alt.Legend(padding=5))
            ).properties(
                width=width_formula,
                height=700
            )

            if modus == "save":
                chart1.save(f'results/gannts/{file_name}.png')

            if modus == "show":
                altair_viewer.show(chart1)

