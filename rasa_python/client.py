# coding=UTF-8
import requests
import json



#url = "http://163.18.26.135:7788/rasa_nlu_train"
#url = "http://163.18.26.135:7788/rasa_chat"
#url = "http://163.18.26.135:7788/db_to_rasa_data"
#url = "http://163.18.26.135:7788/model_change"
#url = "http://163.18.26.135:7788/version_check"
url = "http://163.18.26.135:7788/entity_recognition"

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




#print(tt["entities"][0]["confidence_entity"])

#print(result.text["entities"][0]["confidence_entity"])


# 提供簽收單至福雷的相關資訊。
# 提供發貨通知至福雷的相關資訊。
# 提供包裝明細至日月光的相關資訊。
# 福雷的簽收單 包裝明細
#簽收單
#發貨通知

#    - 提供[簽收單](Tracking)至[福雷](Site)的相關資訊
