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
from data_to_rasa_v3 import *
import time
import subprocess
import shlex #參數形式
import configparser
app = Flask(__name__)

config = configparser.ConfigParser()
config.read('set.conf')
rasa_chat_host = config["Rasa"]["host"]
en_rasa_chat_url = "http://{}:5007/model/parse".format(rasa_chat_host)


# 獲取目錄下的最新文件夾/文件
def new_report(test_report):
    lists = os.listdir(test_report)                                    #列出目錄的下所有文件和文件夾保存到lists
    #print(lists)
    lists.sort(key=lambda fn: os.path.getmtime(test_report + "/" + fn))  # 按时间排序
    file_new = os.path.join(test_report,lists[-1])                     #獲取最新的文件保存到file_new
    return file_new



#==Agent建置==
en_latest=new_report("./rasa_en/models/")
en_nlu_model=new_report(en_latest)
en_nlu_model=en_nlu_model.replace("\\","/")
#==Agent建置==

en_process_pid=0

def rasa_run_en_model():
    global en_process_pid
    global en_nlu_model
    en_cmd="python -m rasa run -m {} --enable-api --log-file out_en.log -p 5007".format(en_nlu_model)
    #使用shlex.split()拆解指令列
    en_args = shlex.split(en_cmd)
    print(en_args)
    #subprocess參數shell=False，執行指令得到的pid就會是系統本身執行的pid
    # shell=True，則開啟另一個子視窗，執行指令時獲取的子視窗pid
    # 因此會造成子進程無法被刪除
    subp = subprocess.Popen(en_args,shell=False,encoding="utf-8")
    #subp = subprocess.Popen(en_args,shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8")
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
    #訓練模型
    status=[]
    for i in range(len(projects)):
        print("tt")
        print(projects[i])
        os.chdir(projects[i])
        #取得現在位置
        """
        train_nlu(config=config_dir,nlu_data=dataset,output=model_dir)
        status.append("success")
        """
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
    en_nlu_model=new_report(model_list[0])
    en_nlu_model=en_nlu_model.replace("\\","/")
    result={"rasa_en":""}#"rasa_zh":"",
    #英文
    try:
        #linux殺死舊模型副程式
        #os.system("kill -9 {}".format(en_process_pid))
        #windows殺死舊模型副程式
        subprocess.call(['taskkill', '/F', '/T', '/PID',  str(en_process_pid)])
        en_cmd="rasa run -m {} --enable-api --log-file out.log -p 5007".format(en_nlu_model)
        en_args = shlex.split(en_cmd)
        print(en_args)
        subp1=subprocess.Popen(en_args,shell=False,encoding="utf-8")
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
    rasa_run_en_model()
    #print(zh_process_pid)
    app.run(host="0.0.0.0", port=7798)