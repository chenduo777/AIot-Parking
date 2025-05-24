# 停車場管理系統 - 完整實現流程

## 📋 專案概述

這是一個基於 YOLOv7 深度學習的智慧停車場管理系統，包含：
- **即時車輛檢測**: 使用 YOLOv7 識別機車和車牌
- **停車狀態管理**: 追蹤 4 個停車位的佔用狀態
- **車牌識別**: 自動識別車牌號碼和顏色
- **費用計算**: 前30分鐘免費，每小時$20
- **API 服務**: 提供 REST API 供前端和行動應用使用

## 🏗️ 系統架構

```
停車場管理系統
├── 硬體層 (樹莓派 + 攝影機)
│   ├── detect_yolov7.py        # YOLOv7 主檢測程式
│   ├── detect_rec_plate.py     # 車牌識別程式
│   └── weights/                # 訓練好的模型檔案
│
├── API 服務層
│   ├── parking_api.py          # Flask API 主程式
│   ├── requirements.txt        # 所有依賴套件
│   └── .gitignore             # Git 忽略檔案
│
├── 測試工具
│   ├── api_test.py            # 本地 API 測試
│   ├── test_production.py     # 正式環境測試
│   └── matplo_place.py        # 停車位可視化
│
└── 部署檔案
    ├── Procfile               # Render 部署設定
    └── render.yaml           # Render 配置檔案
```

---

## 🚀 完整實現流程

### 階段 1: 環境準備與依賴安裝

#### 1.1 建立虛擬環境 (Windows)
```bash
# 切換到專案目錄
cd "d:\school data\NTUT\IoT\final project\project"

# 啟動現有虛擬環境
.\aiotparking\Scripts\activate

# 或建立新的虛擬環境
python -m venv parking_env
parking_env\Scripts\activate
```

#### 1.2 安裝完整依賴套件
```bash
# 安裝所有必要套件
pip install -r requirements.txt

# 驗證核心套件安裝
python -c "import torch, cv2, flask, numpy, shapely; print('✅ 所有套件安裝成功')"
```

#### 1.3 準備模型檔案
確保 `weights/` 資料夾包含：
- `best.pt` - YOLOv7 機車檢測模型
- `yolov7_plate_0421.pt` - 車牌識別模型
- `new_pkg.p` - 停車區域定義檔案

### 階段 2: 本地測試與驗證

#### 2.1 測試 YOLOv7 檢測系統
```bash
# 測試機車檢測 (使用攝影機)
python detect_yolov7.py --source 0 --weights weights/best.pt

# 測試靜態圖片檢測
python detect_yolov7.py --source "test_image.jpg" --weights weights/best.pt
```

#### 2.2 測試車牌識別系統
```bash
# 測試車牌識別
python detect_rec_plate.py --source "platePic" --weights weights/yolov7_plate_0421.pt
```

#### 2.3 啟動 API 服務
```bash
# 啟動本地 API 服務
python parking_api.py
```

API 將在 `http://localhost:5000` 運行，提供以下端點：
- `GET /` - 服務狀態首頁
- `GET /health` - 健康檢查
- `POST /api/parking/update` - 更新停車狀態
- `GET /api/parking/status` - 查詢所有停車位
- `GET /api/parking/my_status?plate=車牌` - 查詢個人狀態

#### 2.4 測試 API 功能
```bash
# 開啟新終端，執行 API 測試
python api_test.py

# 或使用互動式測試工具
python test_production.py
```

### 階段 3: 系統整合測試

#### 3.1 整合檢測與API系統
1. **修改 detect_yolov7.py**，整合 API 呼叫：

```python
import requests

# 在 sendData() 函數中加入 API 呼叫
def sendData():
    # 準備 API 資料格式
    api_data = []
    for result in recognition_results:
        api_data.append({
            "ID": result['ID'],
            "IsOccupied": result['IsOccupied'],
            "LicensePlateNumber": result['LicensePlateNumber']
        })
    
    # 發送到 API
    try:
        response = requests.post(
            'http://localhost:5000/api/parking/update',
            json=api_data,
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            print("✅ API 更新成功")
        else:
            print(f"❌ API 更新失敗: {response.text}")
    except Exception as e:
        print(f"❌ API 連接錯誤: {e}")
```

#### 3.2 完整系統測試流程
```bash
# 1. 啟動 API 服務 (終端 1)
python parking_api.py

# 2. 啟動 YOLOv7 檢測 (終端 2)
python detect_yolov7.py --source 0

# 3. 測試 API 回應 (終端 3)
python test_production.py
```

### 階段 4: 雲端部署 (Render)

#### 4.1 準備部署檔案

建立 `Procfile`：
```
web: gunicorn parking_api:app
```

建立 `.gitignore`：
```
__pycache__/
*.pyc
.env
.venv
platePic/
runs/
weights/*.pt
```

#### 4.2 部署到 GitHub
```bash
# 初始化 Git 倉庫
git init
git add .
git commit -m "Initial commit: 停車場管理系統"

# 推送到 GitHub
git remote add origin https://github.com/你的用戶名/parking-management-api.git
git branch -M main
git push -u origin main
```

#### 4.3 部署到 Render
1. 前往 [Render.com](https://render.com) 並註冊
2. 建立新的 Web Service
3. 連接 GitHub 倉庫
4. 設定部署參數：
   ```
   Name: parking-management-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn parking_api:app
   ```
5. 點擊部署並等待完成

#### 4.4 測試雲端部署
```bash
# 測試雲端 API
python test_production.py
# 選擇選項 2，輸入你的 Render 應用名稱
```

### 階段 5: 生產環境配置

#### 5.1 樹莓派端配置
在樹莓派上修改 `detect_yolov7.py`，指向雲端 API：

```python
# 修改 API 網址
API_URL = "https://parking-management-api-lyvg.onrender.com/api/parking/update"

def sendData():
    # ...existing code...
    response = requests.post(API_URL, json=api_data)
```

#### 5.2 設定自動啟動
建立 `start_detection.sh`：
```bash
#!/bin/bash
cd /home/pi/parking_project
source venv/bin/activate
python detect_yolov7.py --source 0
```

設定開機自動執行：
```bash
# 編輯 crontab
crontab -e

# 加入以下行
@reboot /home/pi/parking_project/start_detection.sh
```

---

## 📱 API 使用指南

### 基礎URL
- **本地開發**: `http://localhost:5000/api`
- **正式環境**: `https://parking-management-api-lyvg.onrender.com/api`

### 主要端點

#### 1. 更新停車狀態 (樹莓派使用)
```http
POST /api/parking/update
Content-Type: application/json

[
  {"ID": 1, "IsOccupied": true, "LicensePlateNumber": "ABC-1234"},
  {"ID": 2, "IsOccupied": false, "LicensePlateNumber": "None"},
  {"ID": 3, "IsOccupied": false, "LicensePlateNumber": "None"},
  {"ID": 4, "IsOccupied": false, "LicensePlateNumber": "None"}
]
```

#### 2. 查詢停車場狀態
```http
GET /api/parking/status
```

回應範例：
```json
[
  {"id": 1, "is_occupied": true, "plate_number": "ABC-1234"},
  {"id": 2, "is_occupied": false, "plate_number": null},
  {"id": 3, "is_occupied": false, "plate_number": null},
  {"id": 4, "is_occupied": false, "plate_number": null}
]
```

#### 3. 查詢個人停車狀態
```http
GET /api/parking/my_status?plate=ABC-1234
```

回應範例：
```json
{
  "is_parked": true,
  "parking_slot": 1,
  "started_at": "2025-05-24 14:00:00",
  "duration_minutes": 85,
  "fee": 20
}
```

## 🎯 未來擴展計劃

### 1. 資料庫整合
- 加入 PostgreSQL 支援
- 實現資料持久化
- 歷史資料分析

### 2. 前端介面
- React.js 管理面板
- 即時狀態顯示
- 手機 App 開發

### 3. 進階功能
- 車牌黑名單
- 預約停車功能
- 電子支付整合

---

## 📞 技術支援

如果遇到問題，請檢查：
1. [故障排除](#故障排除) 章節
2. 查看系統日誌和錯誤訊息
3. 確認所有依賴套件正確安裝
4. 驗證網路連接和 API 可達性

---

## 📄 授權說明

本專案僅供學術研究使用，請勿用於商業用途。

---

*最後更新: 2025年5月24日*