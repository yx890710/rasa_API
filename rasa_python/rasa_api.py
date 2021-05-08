# coding=UTF-8
from flask import Flask,request
import requests
import json
import rasa
import logging
from rasa.cli.scaffold import create_initial_project
from rasa.train import train_nlu
from rasa.model import get_latest_model
import asyncio  #用到了非同步
from rasa.utils.endpoints import EndpointConfig  #從rasa呼叫EndpointConfig
from rasa.core.agent import Agent  #從rasa呼叫Agent
import os
app = Flask(__name__)


#因為用到了非同步等騷操作，這裡還使用了await。反正將rasa返回的對話取出來，挺麻煩
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
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    config_dir=data_dict['config_dir']
    dataset=data_dict['dataset']
    model_dir=data_dict['model_dir']
    try:
        model_path=train_nlu(config=config_dir,nlu_data=dataset,output=model_dir)
        result={"train_nlu":"success","model_dir":model_path}
    except:
        result={"train_nlu":"failed"}
    result_json=json.dumps(result)
    return result_json


@app.route('/rasa_chat',methods=["POST"])
def rasa_chat():
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    message=data_dict["message"]
    nlu_model_dir="./models/nlu/"
    nlu_model=get_latest_model(nlu_model_dir)
    agent = Agent.load(nlu_model,action_endpoint=None)
    result=nlu_chatbot(agent,message)
    result_json=json.dumps({"result":result})
    return result_json




if __name__ == '__main__':
    project = "test-project"
    os.chdir(project)
    print(os.getcwd())
    app.run(host="0.0.0.0", port=8000)
