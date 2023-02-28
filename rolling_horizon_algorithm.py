import pandas as pd
from general import Settings, evaluator_simpy, combine_sequences
from methods.local_search import local_search
from methods.random_search import random_search
from methods.iterated_greedy import iterated_greedy
import numpy as np
import copy
import time


# Algorithm settings
decompose = "per_month_rolling"
setting_list = []
for search_method in ["local_search"]:
    for instance_name in ['120_1', '120_2', '120_3', '120_4', '120_5']:
        setting = Settings(method=f"{decompose}_{search_method}", time_limit=300, stop_criterium="Time", simulator="SimPy",
                           instance=instance_name, objective="Combined")
        setting_list.append(setting)

for setting in setting_list:
    file_name = setting.make_file_name()
    instance = pd.read_pickle(f"factory_data/instances_v3/instance_{setting.instance}.pkl")
    instance_df = instance.convert_to_dataframe()

    start = time.time()
    unique_months = np.unique(instance.DEADLINES)
    print(unique_months)
    best_sequences = {}
    solved_instances = []
    # Apply search strategy per month
    for month in unique_months:
        print(f"Start solving month {month}")
        sub_instance_df = instance_df[instance_df["Deadlines"] == month]
        sub_instance = copy.copy(instance)
        sub_instance.PRODUCT_IDS = sub_instance_df["Product_ID"].tolist()
        sub_instance.DEADLINESs = sub_instance_df["Deadlines"].tolist()
        sub_instance.list_products()
        n = sub_instance.SIZE

        solved_instances.append(sub_instance_df)
        df_for_evaluation = pd.concat(solved_instances)
        plan_for_evaluation = copy.copy(instance)
        plan_for_evaluation.PRODUCT_IDS = df_for_evaluation["Product_ID"].tolist()
        plan_for_evaluation.DEADLINES = df_for_evaluation["Deadlines"].tolist()
        plan_for_evaluation.list_products()

        # Important, the f_eval considers the previously solved subinstances
        f_eval = lambda x, i: evaluator_simpy(plan=plan_for_evaluation, sequence=combine_sequences(best_sequences, x),
                                              seed=setting.seed, objective=setting.objective)

        if setting.method == f"{decompose}_local_search":
            nr_iterations, best_sequence = local_search(n=n, f_eval=f_eval, stop_criterium=setting.stop_criterium,
                                                        budget=setting.budget, time_limit=600, printing=False, write=False)
            print(best_sequence)
        elif setting.method == f"{decompose}_random_search":
            nr_iterations, best_sequence = random_search(n=n, f_eval=f_eval, stop_criterium=setting.stop_criterium,
                                                         budget=setting.budget, time_limit=setting.time_limit, printing=False, write=False)

        elif setting.method == f"{decompose}_iterated_greedy":
            nr_iterations, best_sequence = iterated_greedy(n=n, f_eval=f_eval, stop_criterium=setting.stop_criterium,
                                                         budget=setting.budget, time_limit=setting.time_limit, printing=False, write=False)

        # Save optimized sequence
        best_sequences[month] = best_sequence

    final_sequence = combine_sequences(best_sequences)
    final_fermentation_sequence = np.argsort(final_sequence) + 1
    new_plan = pd.concat(solved_instances)
    new_plan["Fermentation_sequence"] = final_fermentation_sequence
    new_plan.to_csv(f"results/production_sequence/{file_name}.csv")
    plan_for_evaluation = copy.copy(instance)
    plan_for_evaluation.PRODUCT_IDS = new_plan["Product_ID"].tolist()
    plan_for_evaluation.DEADLINES = new_plan["Deadlines"].tolist()
    plan_for_evaluation.list_products()

    # Save results table
    fitness = evaluator_simpy(plan=plan_for_evaluation, sequence=final_sequence, objective=setting.objective,
                              seed=setting.seed, printing=True)
    print(f' after rolling horizon fitness is {fitness}')
    f_eval = lambda x, i: evaluator_simpy(plan=plan_for_evaluation, sequence=x, seed=setting.seed, objective=setting.objective)

    if setting.method == f"{decompose}_local_search":
        nr_iterations, best_sequence = local_search(n=n, f_eval=f_eval, stop_criterium=setting.stop_criterium, budget=setting.time_limit,
                                                    time_limit=600, printing=False, write=False, init=final_sequence)
    elif setting.method == f"{decompose}_random_search":
        nr_iterations, best_sequence = random_search(n=n, f_eval=f_eval, stop_criterium=setting.stop_criterium,
                                                     budget=setting.budget, time_limit=600,
                                                     printing=False, write=False)

    elif setting.method == f"{decompose}_iterated_greedy":
        nr_iterations, best_sequence = iterated_greedy(n=n, f_eval=f_eval, stop_criterium=setting.stop_criterium,
                                                       budget=setting.budget, time_limit=600,
                                                       printing=False, write=False)
    fitness = evaluator_simpy(plan=plan_for_evaluation, sequence=best_sequence, objective=setting.objective,
                              seed=setting.seed, printing=True)

    print(f'after final global search fitness is {fitness}')
    results = pd.DataFrame()
    results['Fitness'] = [fitness]
    results['Time'] = [time.time() - start]
    results['Sequence'] = [best_sequence]
    results.to_csv(f'results/{file_name}.csv', header=True, index=False)


