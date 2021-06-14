# rasa_test
## 內容
* total_word_feature_extractor_zh.dat 請至 [Doctor-Friende](https://github.com/pengyou200902/Doctor-Friende)下載
* model請透過訓練rasa生成模型
## NLU
* 可以分為zh及en兩種
* 設定好data/下的內容、config內容（默認查找config名稱檔案）
    * jieba_userdict及lookup可以識別專有名詞及特別針對專有名詞進行斷詞 
* 執行`rasa train nlu`
    * 模型會以“nlu”開頭存在models資料夾下
* `rasa shell -m models/model_name`
* 開始玩
## rasa_python
* test.py 寫了基礎透過function可以直接建立rasa project、訓練model、與agent對話
* rasa_api.py 寫成api格式，利用事先建立好的project進行模型訓練及對話（若無建立則需利用test.py建立project）
* client.py 測試api的code
