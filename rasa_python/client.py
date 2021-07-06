# coding=UTF-8
import requests
import json



#url = "http://ip:port/rasa_nlu_train"
#url = "http://ip:port//rasa_chat"
#url = "http://ip:port//db_to_rasa_data"
#url = "http://ip:port//model_change"
#url = "http://ip:port//version_check"
url = "http://ip:port//entity_recognition"

#version="20210628"
message="提供簽收單至福雷的相關資訊。"
en_msg="Provide relevant information from POD to Test."

#message=["提供簽收單至福雷的相關資訊。","Provide relevant information from POD to Test."]
#Context_json = json.dumps({"version":version})
#Context_json = json.dumps({"message": message})
Context_json = json.dumps({"zh_text": message,"en_text":en_msg})
#result = requests.post(url)
#Context_json = json.dumps({"b":1000})
result = requests.post(url, data=Context_json)
tt=result.json()
print(tt)


