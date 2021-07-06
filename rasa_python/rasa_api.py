# coding=UTF-8
from flask import Flask,request
import requests
import json
import rasa
import logging
import yaml
from rasa.cli.scaffold import create_initial_project
from rasa.train import train_nlu
from rasa.model import get_latest_model #rasa可以自動偵測最新模型
import asyncio  #用到了非同步
from rasa.utils.endpoints import EndpointConfig  #從rasa呼叫EndpointConfig
from rasa.core.agent import Agent  #從rasa呼叫Agent
import os
from data_to_rasa import *
app = Flask(__name__)


#==Agent建置==
projects=["./rasa_zh/models/v20210628/","./rasa_en/models/v20210628/"]
zh_nlu_model=get_latest_model(projects[0])
en_nlu_model=get_latest_model(projects[1])
zh_agent = Agent.load(zh_nlu_model,action_endpoint=None)
en_agent = Agent.load(en_nlu_model,action_endpoint=None)
#==Agent建置==




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

#========以上部分為對話func部分=====================================================

def entity_process(entity_view,zh_text,en_text):
    # 定義response格式
    data={"rasa_zh":{"text":"","entities":[]},"rasa_en":{"text":"","entities":[]}}
    zh_entity_list=[]
    en_entity_list=[]
    data["rasa_zh"]["text"]=zh_text
    data["rasa_en"]["text"]=en_text
    for i in entity_view:
        # 中文
        try:
            entity_data={"entity_class":"","start_index":0,"end_index":0}
            start_z=zh_text.index(i.zh_Entity)
            end_z=start_z+len(i.zh_Entity)
            entity_data["entity_class"]=i.EntityClass
            entity_data["start_index"]=start_z
            entity_data["end_index"]=end_z
            zh_entity_list.append(entity_data)
        except:
            continue
        # 英文
        try:
            entity_data={"entity_class":"","start_index":0,"end_index":0}
            start_e=en_text.index(i.en_Entity)
            end_e=start_e+len(i.en_Entity)
            entity_data["entity_class"]=i.EntityClass
            entity_data["start_index"]=start_e
            entity_data["end_index"]=end_e
            en_entity_list.append(entity_data)
        except:
            continue
    data["rasa_zh"]["entities"]=zh_entity_list
    data["rasa_en"]["entities"]=en_entity_list
    return data


#========以上部分為實體識別func部分=====================================================

# 靜態文件轉換API
@app.route('/db_to_rasa_data',methods=["POST"])
def db_to_rasa_data():
    #request data
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    v=data_dict["version"]
    #建立中英文資料夾
    zh_mkdir_rasa(v)
    en_mkdir_rasa(v)
    r1=zh_process(v)
    r2=en_process(v)

    result_json=json.dumps({"result_zh":r1,"rasa_en":r2})
    return result_json


# 訓練API
@app.route('/rasa_nlu_train',methods=["POST"])
def rasa_nlu_train():
    projects=["rasa_zh","rasa_en"]
    model_path=[]
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    v=data_dict["version"]
    config_dir = "./config.yml"
    dataset = "./data_{}/".format(v)
    model_dir = "./models/v{}".format(v)
    #config 修改
    config_name="./rasa_zh/config"
    with open(config_name+'.yml','r') as ttfile:
        data_loaded = yaml.safe_load(ttfile)

    data_loaded["pipeline"][0]["dictionary_path"]=dataset+"jieba_userdict" #修改位置
    #直接覆寫檔案
    with open(config_name+'.yml', 'w') as f:
        yaml.dump(data_loaded, f, Dumper=yaml.CDumper)
    #訓練模型
    status=[]
    for i in range(len(projects)):
        print("tt")
        print(projects[i])
        os.chdir(projects[i])
        #取得現在位置
        try:
            train_nlu(config=config_dir,nlu_data=dataset,output=model_dir)
            status.append("success")
        except:
            status.append("failed")
        os.chdir('..')
    result={"rasa_zh":status[0],"rasa_en":status[1]}
    result_json=json.dumps(result)
    return result_json


# 對話API
@app.route('/rasa_chat',methods=["POST"])
def rasa_chat():
    global zh_agent
    global en_agent
    result=[]
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    message=data_dict["message"]
    result={"rasa_zh":"","rasa_en":""}
    try:
        zhresult=nlu_chatbot(zh_agent,message[0])
        result["rasa_zh"]=zhresult
    except:
        result["rasa_zh"]="failed"
    try:
        enresult=nlu_chatbot(en_agent,message[1])
        result["rasa_en"]=enresult
    except:
        result["rasa_en"]="failed"
    result_json=json.dumps(result)
    return result_json


# 模型更換API
@app.route('/model_change',methods=["POST"])
def model_change():
    global zh_agent
    global en_agent
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    v=data_dict["version"]
    model_list=["./rasa_zh/models/v{}/".format(v),"./rasa_en/models/v{}/".format(v)]
    result={"rasa_zh":"","rasa_en":""}
    try:
        zh_agent = Agent.load(get_latest_model(model_list[0]),action_endpoint=None)
        result["rasa_zh"]="success"
    except:
        result["rasa_zh"]="failed"
    try:
        en_agent = Agent.load(get_latest_model(model_list[1]),action_endpoint=None) 
        result["rasa_en"]="success"
    except:
        result["rasa_en"]="failed"
    result_json=json.dumps(result)
    return result_json

# 模型版本確認
@app.route('/version_check',methods=["POST"])
def version_check():
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    v=data_dict["version"]
    zh_path="./rasa_zh/models/"
    en_path="./rasa_en/models/"
    zh_model_listdir=os.listdir(zh_path)
    en_model_listdir=os.listdir(en_path)
    model_version="v"+v
    result={"rasa_zh":"","rasa_en":""}
    for i in zh_model_listdir:
        if model_version.find(i)!=-1 and os.listdir(zh_path+i)!=[]:
            result["rasa_zh"]="existed"
            break
        else:
            result["rasa_zh"]="error"
            continue
    for i in en_model_listdir:
        if model_version.find(i)!=-1 and os.listdir(en_path+i)!=[]:
            result["rasa_en"]="existed"
            break
        else:
            result["rasa_en"]="error"
            continue
    result_json=json.dumps(result)
    return result_json

# 自動萃取實體
@app.route('/entity_recognition',methods=["POST"])
def entity_recognition():
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    zh_text=data_dict["zh_text"]
    en_text=data_dict["en_text"]
    #連結資料庫
    Entity=session.query(Entity_View).all()
    result=entity_process(Entity,zh_text,en_text)
    result_json=json.dumps(result)
    return result_json
    



if __name__ == '__main__':
    print(os.getcwd())
    app.run(host="0.0.0.0", port=7788)
