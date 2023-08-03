import json

json_stochastic = json.load(open('factory_data/data.json', 'r'))

for i in range(len(json_stochastic['products'])):
    for j in range(len(json_stochastic['products'][i]['activities'])):
        mean = json_stochastic['products'][i]['activities'][j]['processing_time'][0]
        json_stochastic['products'][i]['activities'][j]["distribution"]= {
            "type": "NORMAL",
            "args": {
                "mean": float(mean),
                "variance": 1
            }
        }

json.dump(json_stochastic, open('factory_data/stochastic/data_stochastic.json', 'w'))
