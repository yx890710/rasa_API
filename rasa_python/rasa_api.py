# coding=UTF-8
from flask import Flask,request
import requests
import json
import rasa
import logging
from rasa.cli.scaffold import create_initial_project
from rasa.train import train_nlu
from rasa.model import get_latest_model #rasa可以自動偵測最新模型
import asyncio  #用到了非同步
from rasa.utils.endpoints import EndpointConfig  #從rasa呼叫EndpointConfig
from rasa.core.agent import Agent  #從rasa呼叫Agent
import os
app = Flask(__name__)


#因為用到了非同步等騷操作，這裡使用await將rasa返回的對話取出來
async def chatbot(agent,message):
    result = await agent.parse_message_using_nlu_interpreter(message)
    return result

#與chatbot對話
def nlu_chatbot(agent,message):
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    #使用run_until_complete取出返回的資訊
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(chatbot(agent,message))
    return result




@app.route('/rasa_nlu_train',methods=["POST"])
def rasa_nlu_train():
    os.chdir("rasa_en")
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    config_dir=data_dict['config_dir']
    dataset=data_dict['dataset']
    model_dir=data_dict['model_dir']
    model_path=train_nlu(config=config_dir,nlu_data=dataset,output=model_dir)
    """
    try:
        model_path=train_nlu(config=config_dir,nlu_data=dataset,output=model_dir)
        result={"train_nlu":"success","model_dir":model_path}
    except:
        result={"train_nlu":"failed"}
    """
    result={"train_nlu":"success","model_dir":model_path}
    result_json=json.dumps(result)
    return result_json


@app.route('/rasa_chat',methods=["POST"])
def rasa_chat():
    result=[]
    projects=["./rasa_zh/models/zh/","./rasa_en/models/en/"]
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    message=data_dict["message"]
    for i in range(len(projects)):
        nlu_model=get_latest_model(projects[i])
        agent = Agent.load(nlu_model,action_endpoint=None)
        result.append(nlu_chatbot(agent,message[i]))
    result_json=json.dumps({"result_zh":result[0],"rasa_en":result[1]})
    return result_json




if __name__ == '__main__':
    print(os.getcwd())
    app.run(host="0.0.0.0", port=7788)
