import sys
import logging
import re
from typing import Text, Dict, Any

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from py2neo import Graph
from markdownify import markdownify as md

logger = logging.getLogger(__name__)

p = 'data/slot/express.txt'
ord_no='data/slot/ord_no.txt'
express_name = [i.strip() for i in open(p, 'r', encoding='UTF-8').readlines()]
ordno_name = [i.strip() for i in open(ord_no, 'r', encoding='UTF-8').readlines()]
# default neo4j account should be user="neo4j", password="neo4j"
question=["如何查詢與出貨運輸狀況相關問題？","如何查詢與出貨資料查詢相關問題？","查詢三大快遞貨件的結果。"]


def retrieve_disease_name(name):
    names = []
    name = '.*' + '.*'.join(list(name)) + '.*'
    pattern = re.compile(name)
    for i in disease_names:
        candidate = pattern.search(i)
        if candidate:
            names.append(candidate.group())
    return names


def make_button(title, payload):
    return {'title': title, 'payload': payload}




class ActionDonKnow(Action):
    def name(self) -> Text:
        return "action_donknow"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        # dispatcher.utter_template("utter_donknow", tracker)
        dispatcher.utter_message(template="utter_donknow")
        # dispatcher.utter_template("utter_howcanhelp", tracker)
        dispatcher.utter_message(md("您可以向我提問： <br/>如何查詢與出貨運輸狀況相關問題？<br/>\
                                      如何查詢與出貨資料查詢相關問題？<br/>\
                                      查詢三大快遞貨件的結果。"))
        return []


#- action_search_package_date
#  - action_check_express
#  - action_enter_order_number


class ActionSearchPackageDate(Action):
    def name(self) -> Text:
        return "action_search_package_date"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        buttons = []
        for d in question:
            buttons.append(make_button(d, '/search_express'))
        dispatcher.utter_button_message("請選取想要查詢的項目，若没有想要的，请忽略此消息", buttons)
        
        return []

class ActionCheckExpress(Action):
    def name(self) -> Text:
        return "action_check_express"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        express=tracker.get_slot("express")
        if express in express_name:
            template = "請您輸入{0}單號，如需多筆查詢請以『，』分隔。"
            retmsg = template.format(express)
        else:
            template = "暫無{0}的快遞資訊"
            retmsg = template.format(express)
        dispatcher.utter_message(retmsg)     
        return []

class ActionEnterOrderNumber(Action):
    def name(self) -> Text:
        return "action_enter_order_number"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        ord_no=tracker.get_slot("ord_no")
        if ord_no in ordno_name:
            template = "以下為查詢結果：\n{0}已送達"
            retmsg = template.format(ord_no)
        else:
            template = "暫無{0}的單號資訊"
            retmsg = template.format(ord_no)
        dispatcher.utter_message(retmsg)  
        
        return []

