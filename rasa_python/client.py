# coding=UTF-8
import requests
import json



#url = "http://IP:PORT/rasa_nlu_train"
url = "http://IP:PORT/rasa_chat"
#url = "http://IP:PORT/db_to_rasa_data"
#url = "http://IP:PORT/model_change"
#url = "http://IP:PORT/version_check"

version="20210628"
#message="提供簽收單至福雷的相關資訊。"
message=["提供簽收單至福雷的相關資訊。","Provide relevant information from PL to ASE."]
#Context_json = json.dumps({"version":version})
Context_json = json.dumps({"message": message})
#result = requests.post(url)
#Context_json = json.dumps({"b":1000})
result = requests.post(url, data=Context_json)
tt=result.json()
print(tt)


