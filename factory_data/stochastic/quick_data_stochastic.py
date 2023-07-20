import json

json_stochastic = json.load(open('factory_data/data.json', 'r'))

for i in range(len(json_stochastic['FACTORIES'][0]['PRODUCTS'])):
    for j in range(len(json_stochastic['FACTORIES'][0]['PRODUCTS'][i]['ACTIVITIES'])):
        mean = json_stochastic['FACTORIES'][0]['PRODUCTS'][i]['ACTIVITIES'][j]['PROCESSING_TIME'][0]
        json_stochastic['FACTORIES'][0]['PRODUCTS'][i]['ACTIVITIES'][j]["DISTRIBUTION"]= {
            "TYPE": "NORMAL",
            "ARGS": {
                "MEAN": float(mean),
                "VARIANCE": 1
            }
        }

json.dump(json_stochastic, open('factory_data/stochastic/data_stochastic.json', 'w'))
