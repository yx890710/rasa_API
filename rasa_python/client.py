# coding=UTF-8
import requests
import json



url = "http://163.18.26.234:8000/rasa_nlu_train"
#url = "http://163.18.26.234:8000/rasa_chat"
configs = "./config.yml"
training_files = "./data/"
domain = "./domain.yml"
output = "./models/nlu/"
message="我想查詢DN資料"
Context_json = json.dumps({"config_dir": configs,"dataset": training_files,"model_dir": output})
#Context_json = json.dumps({"message": message})
result = requests.post(url, data=Context_json)
tt=result.json()
print(tt)

#print(tt["entities"][0]["confidence_entity"])

#print(result.text["entities"][0]["confidence_entity"])