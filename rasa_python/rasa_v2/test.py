import rasa
import logging
from rasa.cli.scaffold import create_initial_project
from rasa.train import train_nlu
from rasa.model import get_latest_model
import asyncio  #用到了非同步
from rasa.utils.endpoints import EndpointConfig  #從rasa呼叫EndpointConfig
from rasa.core.agent import Agent  #從rasa呼叫Agent
import os



#rasa train data路徑位置==============
configs = "config.yml"
training_files = "data/"
domain = "domain.yml"
output = "models/nlu/"
logfile = 'nlu_model.log'
#config============


# 初次建立rasa project
def create_init_project(project_dir):
    create_initial_project(project_dir)
    # move into project directory and show files
    print(os.listdir("."))

#訓練rasa model(nlu+core)
def train(domain,config,training_files,output):
    model_path = rasa.train(domain, config, [training_files], output)
    print(model_path)

#訓練nlu rasa model
def nlu_train(config,training_files,model_dir):
    model_path=train_nlu(config=config,nlu_data=training_files,output=model_dir)
    print(model_path)

#因為用到了非同步等騷操作，這裡還使用了await。反正將rasa返回的對話取出來，挺麻煩
async def chatbot(message):
    result = await agent.parse_message_using_nlu_interpreter(message)
    return result

#與chatbot對話
def nlu_chatbot(message):
    #message = request.args.get('message')
    #使用run_until_complete取出返回的資訊
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(chatbot(message))
    return result




if __name__ == "__main__":
    project = "test-project"
    #create_init_project(project)
    os.chdir(project)
    print(os.getcwd())
    #train(domain,config,training_files,output)
    nlu_train(configs,training_files,output)
    #nlu_model_dir="./models/nlu/"
    #取得最新model
    #nlu_model=get_latest_model(nlu_model_dir)
    #將上面兩個引數裝載之後，一個後臺實時待命的聊天機器人就設定好了
    #agent = Agent.load(nlu_model,action_endpoint=None)
    #print(nlu_chatbot("12345567831"))
    


    
    
    