import altair_viewer
import pandas as pd
import altair as alt
from classes.general import Settings
"""
This script can be used to make a gannt chart from the resource usage table
for a specific solution to a problem instance. 
It requires the altair_viewer / altair package
"""

simulator_name = "simulator_3"

modus = "save"
settings_list = []
for factory_name in ["factory_1"]:
    for seed in range(1, 2):
        for size in [20]:
            for id in range(1, 2):
                for method in ["local_search"]:
                    for init in ["random"]:
                        for (l1, l2) in [(0.5, 0.5)]:
                            setting = Settings(method=method, stop_criterium="Budget", budget=100 * (size / 20),
                                               instance=f'{size}_{id}_{factory_name}', size=size, simulator="SimPyClaimOneByOneWithDelay",
                                               objective=f'l1={l1}_l2={l2}', init=init, seed=seed, l1=l1, l2=l2)
                            settings_list.append(setting)

for setting in settings_list:
    # determine file name
    file_name = setting.make_file_name()
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

