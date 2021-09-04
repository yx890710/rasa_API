# coding=UTF-8
from flask import Flask,request
import yaml
import pymysql
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy import create_engine
from Sentence_orm import *
import re
import itertools
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
session = Session()
#==DB CONFIG==


#中文+處理有實體的句子
def zh_have_entity_data(view_table):
    h_e_uqid=[]
    h_e_uq_id_list=[]
    for i in view_table:
        if "$<" in i.UserQuestion:
            #print(h_e_uqid)
            if i.UserQuestionID in h_e_uqid:
                continue
            intent_data={"intent_id":"{}${}".format(i.Intent,i.IntentID),"text":i.UserQuestion}
            h_e_uq_id_list.append(intent_data)
            h_e_uqid.append(i.UserQuestionID)
    return h_e_uq_id_list


#替換func
def replaceFomat(text: str, word: str, n: int,reverse=False):
    '''
    Params:
    ---
    text
        要替换的文本
    word
        目标单词
    n
        目标单词的序号
    reverse
        是否进行替回
    Return:
    ---
    new_text
        替换后的文本
    '''
    # 构造【中间变量】
    new_text = text[ : ]
    fmt = "<{}>".format(n)
    # 替换
    if reverse is False:
        new_text = new_text.replace(word, fmt)  # 格式化替换
        return new_text
    # 替回
    elif reverse is True:
        new_text = new_text.replace(fmt, word)  # 去格式化替换
        return new_text
    # 要求非法，引发异常
    else:
        raise TypeError

# 批次替換
def replaceMulti(text: str, olds: list, news: list):
    '''
    Params:
    ---
    text
        要替换的文本
    olds
        旧字符串列表
    news
        新字符串列表
    Return:
    ---
    new_text: str
        替换后的文本
    '''
    if len(olds) != len(news):
        raise IndexError
    else:
        new_text = text[ : ]
        # 格式化替换
        i = 0  # 单词计数器
        for word in olds:
            i += 1
            new_text = replaceFomat(new_text, word, i)
        # 去格式化替回
        i = 0  # 归零
        for word in news:
            i += 1
            new_text = replaceFomat(new_text, word, i,True)
        # 返回替换好的文本
        return new_text



#將實體類別與實體value轉成dict，ex:{EntityClass:[zh_Entity]}
def zh_entity_list(entity_table):
    zh_entity_list={}
    for i in entity_table:
        if i.EntityClass in zh_entity_list:
            continue
        else:
            zh_entity_list[i.EntityClass]=[]
    for i in entity_table:
        for j in zh_entity_list:
            if i.EntityClass==j:
                zh_entity_list[j].append(i.zh_Entity)
    return zh_entity_list


#input:句子，output：[$<EntityClass>]
def extract_entity(sentence):
    entity_class_list=re.findall("\$<[A-Za-z]*>",sentence)
    return entity_class_list


#確認使用類別，並使用特定格式前述extract_entity(sentence)出結果的格式，便於後續進行replace
def extract_data(entity_class_list,entity_value_list):
    use_class=[]
    data_list=[]
    tt_test=[]
    for i in entity_class_list:
        for j in entity_value_list:
            if j in i:
                data_value=[]
                use_class.append(j)
                for k in entity_value_list[j]:
                    data_value.append(k)
                tt_test.append(data_value)
    
    data_list=list(itertools.product(*tt_test))
    
    return use_class,data_list

# 將$<EntityClass>更換為Entity
def replace_entity(sentence,entity_class_list,data_list):
    sentence_list=[]
    for i in data_list:
        a=replaceMulti(sentence,entity_class_list,i)
        sentence_list.append(a)
    return sentence_list


#具有實體建立出的多個使用者句，進行標注實體以及實體位置查找
def entity_start_end(intent_id,sentence_list,class_list,data_list):
    zh_nlu_intent_list=[]
    for i in range(len(sentence_list)):
        zh_nlu_entity_list=[]
        zh_nlu_intent={"text":"","intent":"","entities":[]}
        zh_nlu_intent["text"]=sentence_list[i]
        zh_nlu_intent["intent"]=str(intent_id)
        #print(data_list[i])
        for k in range(len(class_list)):
            zh_nlu_entity={"end":0,"entity":"","start":0,"value":"","extractor":"DIETClassifier"}
            if data_list[i][k]=="":
                break
            else:
                zh_nlu_entity["start"]=sentence_list[i].find(data_list[i][k])
                zh_nlu_entity["end"]=sentence_list[i].find(data_list[i][k])+len(data_list[i][k])
                zh_nlu_entity["value"]=data_list[i][k]
                zh_nlu_entity["entity"]=class_list[k]
                zh_nlu_entity_list.append(zh_nlu_entity)
        zh_nlu_intent["entities"]=zh_nlu_entity_list
        zh_nlu_intent_list.append(zh_nlu_intent)
    return zh_nlu_intent_list

#========以上部分為多個實體處理意圖的方式


def zh_no_entity_intent(view_table):
    zh_nlu_intent_list=[]
    for i in view_table:
        if i.EntityClassID==None:
            zh_nlu_intent={"text":"","intent":"","entities":[]}
            zh_nlu_intent["intent"]="{}${}".format(i.Intent,i.IntentID)
            zh_nlu_intent["text"]=i.UserQuestion
            zh_nlu_intent_list.append(zh_nlu_intent)
    return zh_nlu_intent_list

# nlu.json內的lookup table處理
def lookup_table(version,entity_table):
    lookup_list=[]
    class_list=[]
    for i in entity_table:
        if i.EntityClass in class_list:
            continue
        else:
            lookup={"name":"","elements":"data_{}/lookup_zh/%.txt".format(version)}
            lookup["name"]=i.EntityClass
            lookup["elements"]=lookup["elements"].replace("%",i.EntityClass)
            lookup_list.append(lookup)
            class_list.append(i.EntityClass)
    return class_list,lookup_list

# lookup txt檔處理
def lookup_txt(lng,entity_value_list,version,lookup_name):
    for i in entity_value_list:
        f = open('./rasa_{0}/data_{1}/lookup_{2}/{3}.txt'.format(lng,version,lookup_name,i),'w+')
        for item in entity_value_list[i]:
            f.write("%s\n" % item)
        f.close()

# jieba斷詞
def lookup_jieba(lng,entity_value_list,version):
    for i in entity_value_list:
        f = open('./rasa_{0}/data_{1}/jieba_userdict/{2}.txt'.format(lng,version,i),'w+')
        for item in entity_value_list[i]:
            f.write("%s 18000 nz\n" % item)
        f.close()


def domain_data(view_table,class_list):
    id_list=[]
    for i in view_table:
        if i.IntentID in id_list:
            continue
        dd="{}${}".format(i.Intent,i.IntentID)
        id_list.append(dd)
    #print(id_list)
    domain={'version': '2.0', 'intents': [], 'entities': [], 'session_config': {'session_expiration_time': 60, 'carry_over_slots_to_new_session': True}}
    domain['intents']=id_list
    domain['entities']=class_list
    return domain

#建立中文資料夾
def zh_mkdir_rasa(version):
    path_list=["./rasa_zh/data_{}".format(version),"./rasa_zh/data_{}/lookup_zh".format(version),"./rasa_zh/data_{}/jieba_userdict".format(version)]
    for path in path_list:
        if not os.path.isdir(path):
            os.mkdir(path)




def zh_process(version):
    zh_intent_list=[]
    view=session.query(Rasa_View).all()  
    Entity=session.query(Entity_View).all()
    #處理沒有實體的意圖
    zh_intent_list.extend(zh_no_entity_intent(view))
    #處理有實體的部分
    have_entity_datalist=zh_have_entity_data(view)
    entity_value_list=zh_entity_list(Entity)
    for i in have_entity_datalist:
        e_list=extract_entity(i["text"])
        entity_class,data_list=extract_data(e_list,entity_value_list)
        sentence_list=replace_entity(i["text"],e_list,data_list)
        zh_intent_list.extend(entity_start_end(i["intent_id"],sentence_list,entity_class,data_list))
    
    #lookup table+實體類別儲存（後續存lookup txt會使用到）
    class_list,lookup=lookup_table(version,Entity)
    #nlu.json模板，將資料塞入
    nlu={"rasa_nlu_data":{"common_examples":zh_intent_list,"lookup_tables":lookup}}
    #print(nlu)
    #print(type(nlu))
    #輸出json檔
    
    filename="./rasa_zh/data_{}/nlu".format(version)    
    with open(filename+'.json','w+') as outfile:
        json.dump(nlu,outfile,ensure_ascii=False)
        outfile.write('\n')

    # lookup txt檔案
    lookup_txt("zh",entity_value_list,version,"zh")
    #jieba檔案
    lookup_jieba("zh",entity_value_list,version)

    return "success"

#========以上部分為中文處理部分=====================================================

#處理無實體的句子
def en_no_entity_intent(view_table):
    en_nlu_intent_list=[]
    for i in view_table:
        if i.EntityClassID==None:
            en_nlu_intent={"text":"","intent":"","entities":[]}
            en_nlu_intent["intent"]="{}${}".format(i.Intent,i.IntentID)
            en_nlu_intent["text"]=i.English_UserQuestion
            en_nlu_intent_list.append(en_nlu_intent)
    return en_nlu_intent_list


#英文+處理有實體的句子
def en_have_entity_data(view_table):
    h_e_uqid=[]
    h_e_uq_id_list=[]
    for i in view_table:
        if "$<" in i.English_UserQuestion:
            #print(h_e_uqid)
            if i.UserQuestionID in h_e_uqid:
                continue
            intent_data={"intent_id":"{}${}".format(i.Intent,i.IntentID),"text":i.English_UserQuestion}
            h_e_uq_id_list.append(intent_data)
            h_e_uqid.append(i.UserQuestionID)
    return h_e_uq_id_list

#將實體類別與實體value轉成dict，ex:{EntityClass:[zh_Entity]}
def en_entity_list(entity_table):
    en_entity_list={}
    for i in entity_table:
        if i.EntityClass in en_entity_list:
            continue
        else:
            en_entity_list[i.EntityClass]=[]
    for i in entity_table:
        for j in en_entity_list:
            if i.EntityClass==j:
                en_entity_list[j].append(i.en_Entity)
    return en_entity_list


# nlu.json內的lookup table處理
def en_lookup_table(version,entity_table):
    lookup_list=[]
    class_list=[]
    for i in entity_table:
        if i.EntityClass in class_list:
            continue
        else:
            lookup={"name":"","elements":"data_{}/lookup_en/%.txt".format(version)}
            lookup["name"]=i.EntityClass
            lookup["elements"]=lookup["elements"].replace("%",i.EntityClass)
            lookup_list.append(lookup)
            class_list.append(i.EntityClass)
    return class_list,lookup_list


#建立英文資料夾
def en_mkdir_rasa(version):
    path_list=["./rasa_en/data_{}".format(version),"./rasa_en/data_{}/lookup_en".format(version)]
    for path in path_list:
        if not os.path.isdir(path):
            os.mkdir(path)

def en_process(version):
    en_intent_list=[]
    view=session.query(Rasa_View).all()  
    Entity=session.query(Entity_View).all()
    #處理沒有實體的意圖
    en_intent_list.extend(en_no_entity_intent(view))
    #處理有實體的部分
    have_entity_datalist=en_have_entity_data(view)
    entity_value_list=en_entity_list(Entity)
    for i in have_entity_datalist:
        e_list=extract_entity(i["text"])
        entity_class,data_list=extract_data(e_list,entity_value_list)
        sentence_list=replace_entity(i["text"],e_list,data_list)
        en_intent_list.extend(entity_start_end(i["intent_id"],sentence_list,entity_class,data_list))
    
    #lookup table+實體類別儲存（後續存lookup txt會使用到）
    class_list,lookup=en_lookup_table(version,Entity)
    #nlu.json模板，將資料塞入
    nlu={"rasa_nlu_data":{"common_examples":en_intent_list,"lookup_tables":lookup}}
    #print(nlu)
    #print(type(nlu))
    #輸出json檔
    filename="./rasa_en/data_{}/nlu".format(version)    
    with open(filename+'.json','w+') as outfile:
        json.dump(nlu,outfile,ensure_ascii=False)
        outfile.write('\n')

    # lookup txt檔案
    lookup_txt("en",entity_value_list,version,"en")

    return "success"


#========以上部分為英文處理部分=====================================================

"""

@app.route('/db_to_rasa_data',methods=["POST"])
def db_to_rasa_data():
    #request data
    data=bytes.decode(request.data)
    data_dict = json.loads(data)
    v=data_dict["version"]
    print(v)
    #建立中英文資料夾
    zh_mkdir_rasa(v)
    en_mkdir_rasa(v)
    r1=zh_process(v)
    r2=en_process(v)

    result_json=json.dumps({"result_zh":r1,"rasa_en":r2})
    return result_json



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7787)
    
"""