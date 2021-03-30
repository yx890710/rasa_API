# rasa_test
## 內容
* total_word_feature_extractor_zh.dat 請至 [Doctor-Friende](https://github.com/pengyou200902/Doctor-Friende)下載
* model請透過訓練rasa生成模型
* 測試文件放在rasa_chatbot.xlsx檔案
## NLU
* 設定好data/下的內容、config內容（默認查找config名稱檔案）
* 執行`rasa train nlu`
    * 模型會以“nlu”開頭存在models資料夾下
* `rasa shell -m models/model_name`
* 開始玩
