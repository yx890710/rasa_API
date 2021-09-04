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
from data_to_rasa_v4 import *
import time
import subprocess
import shlex #參數形式
app = Flask(__name__)

#zh_rasa_chat_url = "http://ip:5005/model/parse"
en_rasa_chat_url = "http://ip:5007/model/parse"


# 獲取目錄下的最新文件夾/文件
def new_report(test_report):
    lists = os.listdir(test_report)                                    #列出目錄的下所有文件和文件夾保存到lists
    #print(lists)
    lists.sort(key=lambda fn: os.path.getmtime(test_report + "/" + fn))  # 按时间排序
    file_new = os.path.join(test_report,lists[-1])                     #獲取最新的文件保存到file_new
    return file_new



#==Agent建置==

#en_latest=new_report("./rasa_en/models/v2021-07-15_20:45:43")
#en_nlu_model=get_latest_model(en_latest)
#loop = asyncio.get_event_loop()
#zh_agent = Agent.load(zh_nlu_model,action_endpoint=None)
#en_agent = Agent.load(en_nlu_model,action_endpoint=None)
#zh_latest=new_report("./rasa_zh/models/")
#zh_nlu_model=get_latest_model(zh_latest)

en_latest=new_report("./rasa_en/models/")
en_nlu_model=get_latest_model(en_latest)
#==Agent建置==

#zh_process_pid=0
en_process_pid=0


"""
def rasa_run_zh_model():
    global zh_process_pid
    global zh_nlu_model
    zh_cmd="rasa run -m {} --enable-api --log-file out_zh.log -p 5005".format(zh_nlu_model)
    #使用shlex.split()拆解指令列
    zh_args = shlex.split(zh_cmd)
    print(zh_args)
    #subprocess參數shell=False，執行指令得到的pid就會是系統本身執行的pid
    # shell=True，則開啟另一個子視窗，執行指令時獲取的子視窗pid
    # 因此會造成子進程無法被刪除
    subp = subprocess.Popen(zh_args,shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8")
    zh_process_pid=subp.pid
    print(zh_process_pid)
    print(zh_nlu_model)
"""

def rasa_run_en_model():
    global en_process_pid
    global en_nlu_model
    en_cmd="rasa run -m {} --enable-api --log-file out_en.log -p 5007".format(en_nlu_model)
    #使用shlex.split()拆解指令列
    en_args = shlex.split(en_cmd)
    print(en_args)
    #subprocess參數shell=False，執行指令得到的pid就會是系統本身執行的pid
    # shell=True，則開啟另一個子視窗，執行指令時獲取的子視窗pid
    # 因此會造成子進程無法被刪除
    subp = subprocess.Popen(en_args,shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8")
    en_process_pid=subp.pid
    print(en_process_pid)
    print(en_nlu_model)

#========以上部分為配置rasa Server func部分=====================================================


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
    for i in entity_view:
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

"""
def rasa_zh_chat(zh_message):
    json_zh_data = {"text": zh_message}
    zh_data = json.dumps(json_zh_data)
    zh_result = requests.post(zh_rasa_chat_url, data=zh_data)
    zh_data=zh_result.json()
    return zh_data
"""

def rasa_en_chat(en_message):
    json_en_data = {"text": en_message}
    en_data = json.dumps(json_en_data)
    en_result = requests.post(en_rasa_chat_url, data=en_data)
    en_data=en_result.json()
    return en_data

#========以上部分為對話func部分=====================================================

# 靜態文件轉換API
@app.route('/db_to_rasa_data',methods=["POST"])
def db_to_rasa_data():
    #request data
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    v=data_dict["version"]
    #建立中英文資料夾
    #zh_mkdir_rasa(v)
    en_mkdir_rasa(v)
    #r1=zh_process(v)
    r2=en_process(v)

    result_json=json.dumps({"rasa_en":r2})#"rasa_zh":r1,
    return result_json


# 訓練API
@app.route('/rasa_nlu_train',methods=["POST"])
def rasa_nlu_train():
    projects=["rasa_en"]#"rasa_zh",
    model_path=[]
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    v=data_dict["version"]
    config_dir = "./config.yml"
    dataset = "./data_{}/".format(v)
    model_dir = "./models/v{}".format(v)
    """
    #config 修改
    config_name="./rasa_zh/config"
    with open(config_name+'.yml','r') as ttfile:
        data_loaded = yaml.safe_load(ttfile)

    data_loaded["pipeline"][0]["dictionary_path"]=dataset+"jieba_userdict" #修改位置
    #直接覆寫檔案
    with open(config_name+'.yml', 'w') as f:
        yaml.dump(data_loaded, f, Dumper=yaml.CDumper)
    """
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
    result={"rasa_en":status[0]}#"rasa_zh":status[0],
    result_json=json.dumps(result)
    return result_json


@app.route('/model_change',methods=["POST"])
def model_change():
    #global zh_process_pid
    #global zh_nlu_model
    global en_process_pid
    global en_nlu_model
    #global subp
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    v=data_dict["version"]
    model_list=["./rasa_en/models/v{}/".format(v)]#"./rasa_zh/models/v{}/".format(v),
    #model_path="./rasa_zh/models/v{}/".format(v)
    #zh_nlu_model=get_latest_model(model_list[0])
    en_nlu_model=get_latest_model(model_list[0])
    result={"rasa_en":""}#"rasa_zh":"",
    #中文
    """
    try:
        #殺死舊模型子進程
        os.system("kill -9 {}".format(zh_process_pid))
        zh_cmd="rasa run -m {} --enable-api --log-file out.log -p 5005".format(zh_nlu_model)
        zh_args = shlex.split(zh_cmd)
        print(zh_args)
        #建立新模型server子進程
        subp=subprocess.Popen(zh_args,shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8")
        zh_process_pid=subp.pid
        print(zh_process_pid)
        result["rasa_zh"]="success"
    except:
        result["rasa_zh"]="failed"
    """
    #英文
    try:
        os.system("kill -9 {}".format(en_process_pid))
        en_cmd="rasa run -m {} --enable-api --log-file out.log -p 5007".format(en_nlu_model)
        en_args = shlex.split(en_cmd)
        print(en_args)
        subp1=subprocess.Popen(en_args,shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8")
        en_process_pid=subp1.pid
        print(en_process_pid)
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
    #zh_path="./rasa_zh/models/"
    en_path="./rasa_en/models/"
    #zh_model_listdir=os.listdir(zh_path)
    en_model_listdir=os.listdir(en_path)
    model_version="v"+v
    result={"rasa_en":""}#"rasa_zh":"",
    """
    for i in zh_model_listdir:
        if model_version.find(i)!=-1 and os.listdir(zh_path+i)!=[]:
            result["rasa_zh"]="existed"
            break
        else:
            result["rasa_zh"]="error"
            continue
    """
    for i in en_model_listdir:
        if model_version.find(i)!=-1 and os.listdir(en_path+i)!=[]:
            result["rasa_en"]="existed"
            break
        else:
            result["rasa_en"]="error"
            continue
    result_json=json.dumps(result)
    return result_json

    
#對話API
@app.route('/rasa_chat',methods=["POST"])
def rasa_chat():
    result=[]
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    result={"rasa_en":""}#"rasa_zh":"",
    #zh_text=data_dict["zh_text"]
    en_text=data_dict["en_text"]
    #result["rasa_zh"]=rasa_zh_chat(zh_text)
    result["rasa_en"]=rasa_en_chat(en_text)
    result_json=json.dumps(result)
    return result_json



if __name__ == '__main__':
    #rasa_run_zh_model()
    rasa_run_en_model()
    #print(zh_process_pid)
    app.run(host="0.0.0.0", port=7798)





"""
#因為用到了非同步等騷操作，這裡使用await將rasa返回的對話取出來
async def chatbot(agent,message):
    result = agent.parse_message_using_nlu_interpreter(message)
    return result

#與chatbot對話
def nlu_chatbot(agent,message):
    #new_loop = asyncio.new_event_loop()
    #asyncio.set_event_loop(new_loop)
    #使用run_until_complete取出返回的資訊
    #loop = asyncio.get_event_loop()
    result = loop.run_until_complete(chatbot(agent,message))
    return result
"""
#========以上部分為對話func部分=====================================================

"""#舊版
# 模型更換API
@app.route('/model_change',methods=["POST"])
def model_change():
    global zh_process_pid
    global zh_nlu_model
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
"""
# 對話API
"""
@app.route('/rasa_chat',methods=["POST"])
def rasa_chat():
    global zh_agent
    global en_agent
    result=[]
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    result={"rasa_zh":"","rasa_en":""}
    zh_text=data_dict["zh_text"]
    zhresult=nlu_chatbot(zh_agent,zh_text)
    result["rasa_zh"]=zhresult
    result_json=json.dumps(result)
    return result_json
"""