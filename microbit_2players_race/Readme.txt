Project: micro:bit 雙人賽跑遊戲
Original author: Josmy
Updated: 2026-10-13
========================================

專案介紹
========

玩家攜帶 micro:bit 跑步或搖動裝置，移動資料會顯示在電腦的賽道畫面上，
最先抵達終點的玩家獲勝。

電腦不直接處理 micro:bit radio。連接電腦的接收端 micro:bit 負責接收
玩家 micro:bit 的無線資料，再透過 USB Serial 傳給 Python 程式。


硬體資料流
==========

玩家 micro:bit × 2
        |
        | micro:bit radio
        v
接收端 micro:bit
        |
        | USB Serial（115200 baud）
        v
Python 遊戲程式
        |
        v
Tkinter 賽道畫面

實體雙人模式共需要三片 micro:bit：

1. 兩片玩家 micro:bit
2. 一片透過 USB 連接電腦的接收端 micro:bit

microbit_programs/player.hex
    玩家端韌體。偵測玩家移動並透過 radio 傳送資料。

microbit_programs/moderator.hex
    接收端韌體。接收 radio 資料並經 USB Serial 傳給電腦。
    moderator 是原始專案沿用的檔名。


主要功能
========

- 最多顯示四名玩家
- 只有一名實體玩家時，自動加入電腦對手
- 三秒倒數後才開始計算玩家移動量
- 玩家可在畫面中選擇角色圖片
- 自動判定冠軍並播放倒數及勝利音效
- 支援全螢幕、視窗及 Demo 模式
- Serial 在背景執行緒讀取
- Tkinter 畫面只在主執行緒更新


系統需求
========

- Python 3.10 以上
- Pillow 10.0 以上
- pygame 2.5 以上
- pyserial 3.5 以上
- 實體雙人模式需要三片 micro:bit


安裝
====

進入程式目錄：

    cd D:\公司行政工作\艾思\microbit_2players_race\microbit_2players_race

建立及啟用虛擬環境（建議）：

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

安裝套件：

    python -m pip install -r requirements.txt


燒錄 micro:bit
================

1. 將 player.hex 分別複製到兩片玩家 micro:bit。
2. 將 moderator.hex 複製到接收端 micro:bit。
3. 使用可傳輸資料的 USB 線將接收端 micro:bit 連接電腦。


執行遊戲
========

一般執行：

    python microbit_1v1_race.py

指定 Serial Port：

    python microbit_1v1_race.py --port COM4

沒有 micro:bit 時，以視窗模式檢查介面：

    python microbit_1v1_race.py --demo --windowed

操作按鍵：

- Start Race：開始倒數及比賽
- Reset：清除玩家及比賽狀態
- F11：切換全螢幕
- Esc 或 Exit：關閉程式


Serial 通訊格式
===============

原始韌體格式：

    player1

代表玩家首次連線。

    player1_3

代表 player1 回報 3 步。Python 會依 DISTANCE_PER_STEP 換算遊戲距離。

電腦端保留原始程式的 Serial 回傳訊息：

    player1_connect ok
    player1_finish
    reset

如果接收端 micro:bit 只負責單向轉送 radio 資料、不處理電腦回傳內容，
這些訊息會被忽略，不影響接收資料。

程式也支援未來可使用的新格式：

    JOIN|player1
    MOVE|player1|3


遊戲狀態
========

    WAITING -> COUNTDOWN -> RACING -> FINISHED
       ^                                  |
       +------------- RESET --------------+

- WAITING：等待玩家連線
- COUNTDOWN：倒數，忽略移動量
- RACING：累計距離並更新畫面
- FINISHED：顯示冠軍並停止接受移動量


程式架構
========

microbit_2players_race/
|-- main.py
|      應用程式入口與事件協調
|-- microbit_1v1_race.py
|      相容原始執行方式的啟動檔
|-- config.py
|      Serial、距離、玩家數及路徑設定
|-- controllers/
|   |-- game_controller.py
|       遊戲狀態、規則與勝負判定
|-- models/
|   |-- game_state.py
|   |-- player.py
|-- services/
|   |-- serial_manager.py
|   |-- protocol.py
|   |-- audio_manager.py
|-- views/
|   |-- game_view.py
|-- tests/
|-- images/
|-- audio/
|-- microbit_programs/


主要設定
========

設定集中在 config.py：

SERIAL_BAUDRATE      115200
MAX_PLAYERS          4
RACE_DISTANCE        1000
DISTANCE_PER_STEP    10
COUNTDOWN_SECONDS    3


執行測試
========

    python -m unittest discover -s tests -v

測試包含：

- 舊版與新版 Serial 訊息解析
- 防止重複新增玩家
- 單人模式加入電腦對手
- 倒數期間不累積距離
- 第一位抵達終點的玩家成為唯一冠軍


常見問題
========

1. 找不到 Serial 裝置

   確認接收端 micro:bit 已使用可傳輸資料的 USB 線連接，並檢查裝置
   管理員中的 COM Port。

2. 同時找到多個 Serial 裝置

   使用 --port 指定接收端 micro:bit：

       python microbit_1v1_race.py --port COM4

3. PowerShell 無法啟用虛擬環境

   可直接使用虛擬環境內的 Python：

       .\.venv\Scripts\python.exe microbit_1v1_race.py
