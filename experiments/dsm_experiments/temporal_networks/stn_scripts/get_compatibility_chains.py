import numpy as np

from temporal_networks.stn import STN


def get_compatibility_chains(stn, productionplan, cp_output):

    for constraint in productionplan.factory.compatibility_constraints:
        constraint_0_activities = cp_output[(cp_output['product_id'] == constraint[0]['product_id']) & (
                    cp_output['activity_id'] == constraint[0]['activity_id'])]
        constraint_1_activities = cp_output[(cp_output['product_id'] == constraint[1]['product_id']) & (
                    cp_output['activity_id'] == constraint[1]['activity_id'])]
        if len(constraint_0_activities) > 0 and len(constraint_1_activities) > 0:
            for index, row in constraint_0_activities.iterrows():
                product_index_0 = row["product_index"]
                activity_id_0 = row["activity_id"]
                start_0 = row['earliest_start']

                for index, row in constraint_1_activities.iterrows():
                    product_index_1 = row["product_index"]
                    activity_id_1 = row["activity_id"]
                    start_1 = row['earliest_start']

                if start_0 < start_1:
                    pred_idx = stn.translation_dict_reversed[(product_index_0, activity_id_0, STN.EVENT_FINISH)]
                    suc_idx = stn.translation_dict_reversed[(product_index_1, activity_id_1, STN.EVENT_START)]

                else:
                    pred_idx = stn.translation_dict_reversed[(product_index_1, activity_id_1, STN.EVENT_FINISH)]
                    suc_idx = stn.translation_dict_reversed[(product_index_0, activity_id_0, STN.EVENT_START)]

                stn.add_interval_constraint(pred_idx, suc_idx, 0, np.inf)

    return stn
