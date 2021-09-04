# coding=UTF-8
from flask import Flask,request
import pymysql
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy import create_engine
from Sentence_orm import *
import re
import json
import configparser


app = Flask(__name__)



#==DB CONFIG==
config = configparser.ConfigParser()
config.read('set.conf')
user = config["DB"]["user"]
password = config["DB"]["password"]
host = config["DB"]["host"]
DB_name = config["DB"]["DB_name"]

DBInfo = "mysql+pymysql://"+ user +":"+password+ "@" + host+ "/" + DB_name+"?charset=utf8mb4"
engine = create_engine(DBInfo, encoding='utf-8')
Session = sessionmaker(bind=engine)
#==DB CONFIG==



def entity_process(entity_view,zh_text,en_text):
    # 定義response格式
    data={"rasa_zh":{"text":"","entities":[]},"rasa_en":{"text":"","entities":[]}}
    zh_entity_list=[]
    en_entity_list=[]
    data["rasa_zh"]["text"]=zh_text
    data["rasa_en"]["text"]=en_text
    dd_zh=[]
    dd_en=[]
    for i in entity_view:
        if i.zh_Entity=="" or i.zh_Entity==None:
            continue
        # 中文
        try:
            if i.zh_Entity in dd_zh:
                continue
            entity_data={"entity_id":"","start_index":0,"end_index":0}
            start_z=zh_text.index(i.zh_Entity)
            dd_zh.append(i.zh_Entity)
            end_z=start_z+len(i.zh_Entity)
            entity_data["entity_id"]=i.EntityClassID
            entity_data["start_index"]=start_z
            entity_data["end_index"]=end_z
            zh_entity_list.append(entity_data)
        except:
            continue
    for i in entity_view:
        if i.zh_Entity=="" or i.zh_Entity==None:
            continue
        # 英文
        try:
            if i.en_Entity in dd_en:
                continue
            entity_data={"entity_id":"","start_index":0,"end_index":0}
            start_e=en_text.index(i.en_Entity)
            dd_en.append(i.en_Entity)
            end_e=start_e+len(i.en_Entity)
            entity_data["entity_id"]=i.EntityClassID
            entity_data["start_index"]=start_e
            entity_data["end_index"]=end_e
            en_entity_list.append(entity_data)
        except:
            continue
    data["rasa_zh"]["entities"]=zh_entity_list
    data["rasa_en"]["entities"]=en_entity_list
    return data


#========以上部分為實體識別func部分=====================================================


# 自動萃取實體
@app.route('/entity_recognition',methods=["POST"])
def entity_recognition():
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    zh_text=data_dict["zh_text"]
    en_text=data_dict["en_text"]
    #連結資料庫
    session = Session()
    Entity_v=session.query(Entity).filter_by(DeleteStatus=0)
    result=entity_process(Entity_v,zh_text,en_text)
    session.close()
    result_json=json.dumps(result)
    return result_json



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7770)