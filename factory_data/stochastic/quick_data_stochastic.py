import json

json_stochastic = json.load(open('factory_data/data.json', 'r'))

for i in range(len(json_stochastic['PRODUCTS'])):
    for j in range(len(json_stochastic['PRODUCTS'][i]['ACTIVITIES'])):
        mean = json_stochastic['PRODUCTS'][i]['ACTIVITIES'][j]['PROCESSING_TIME'][0]
        json_stochastic['PRODUCTS'][i]['ACTIVITIES'][j]["DISTRIBUTION"]= {
            "TYPE": "NORMAL",
            "ARGS": {
                "MEAN": float(mean),
                "VARIANCE": 1
            }
        }

json.dump(json_stochastic, open('factory_data/scenarios/data_stochastic.json', 'w'))
