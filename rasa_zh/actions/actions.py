import sys
import logging
import re
from typing import Text, Dict, Any,List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import AllSlotsReset,SlotSet
from rasa_sdk.executor import CollectingDispatcher
from py2neo import Graph
from markdownify import markdownify as md

logger = logging.getLogger(__name__)

# default neo4j account should be user="neo4j", password="neo4j"
data=["Tracking#快速查詢","依選單條件查詢"]
condition=["HAWB","DN","DropShip number","產品批號Sublot"]

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

class ValidateTForm(Action):
    def name(self) -> Text:
        return "validate_t_form"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        required_slots = ["search_btn", "tracking_condition", "info_search_num"]

        for slot_name in required_slots:
            if tracker.slots.get(slot_name) is None:
                # The slot is not filled yet. Request the user to fill this slot next.
                return [SlotSet("requested_slot", slot_name)]

        # All slots are filled.
        return [SlotSet("requested_slot", None)]


class ActionDataSearch(Action):
    def name(self) -> Text:
        return "action_data_search"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        buttons = []
        for i in data:
            buttons.append(make_button(i,i))
        
        dispatcher.utter_button_message("請選取想要查詢的方式，若没有想要的，请忽略此消息", buttons)

        return []


class ActionTrackingCondition(Action):
    def name(self) -> Text:
        return "action_tracking_condition"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        buttons = []
        for i in condition:
            buttons.append(make_button(i,i))
        dispatcher.utter_button_message("請選取查詢條件，若没有想要的，请忽略此消息", buttons)

        return []



class ActionResult(Action):
    def name(self) -> Text:
        return "action_result"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        search_btn=tracker.get_slot("search_btn")
        tracking_condition=tracker.get_slot("tracking_condition")
        info_search_num=tracker.get_slot("info_search_num")
        print(type(info_search_num))
        msg1 = "已將您欲查詢的貨件資訊彙整如下:\n"
        dispatcher.utter_message(msg1)
        if type(info_search_num) == list:
            for i in info_search_num: 
                if len(i)==10:
                    template="查詢方式：{0}\n查詢條件：{1}\n單號：{2}\n"
                else:
                    template="查詢方式：{0}\n查詢條件：{1}\n單號：{2}，格式錯誤，查詢失敗！\n"
                retmsg = template.format(search_btn,tracking_condition,i)
                dispatcher.utter_message(retmsg) 
        else:
            if len(info_search_num)==10:
                template="查詢方式：{0}\n查詢條件：{1}\n單號：{2}\n"
            else:
                template="查詢方式：{0}\n查詢條件：{1}\n單號：{2}，格式錯誤，查詢失敗！\n"
            retmsg = template.format(search_btn,tracking_condition,info_search_num)
            dispatcher.utter_message(retmsg) 

        return [AllSlotsReset()]
