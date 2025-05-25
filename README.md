# 智慧停車管理系統

## 專案概述

這是一個基於 YOLOv7 物件檢測的智慧停車管理系統，主要功能：
- **車輛辨識檢測**: 使用 YOLOv7 識別車輛與車牌
- **停車位管理**: 管理 4 個停車位的佔用情況
- **車牌辨識**: 自動辨識與記錄車牌號碼
- **收費計算**: 前30分鐘免費，每小時$20
- **API 服務**: 提供 REST API 供外部應用使用

## 系統架構

```
智慧停車管理系統
├── 檢測模組 (樹莓派 + 攝影機)
│   ├── detect_yolov7.py        # YOLOv7 主要監測程式
│   ├── detect_rec_plate.py     # 車牌辨識程式
│   └── weights/                # 訓練好的模型檔案
│
├── API 服務模組
│   ├── parking_api.py          # Flask API 主程式
│   ├── requirements.txt        # 依賴套件列表
│   └── .gitignore             # Git 忽略檔案
│
├── 測試工具
│   ├── api_test.py            # 測試 API 功能
│   ├── test_production.py     # 生產環境測試
│   └── matplo_place.py        # 停車位位置繪製
│
└── 部署檔案
    ├── Procfile               # Render 部署設定
    └── render.yaml           # Render 配置檔案
```

---

## 快速開始指南

### 步驟 1: 準備開發環境

#### 1.1 建立虛擬環境 (Windows)
```bash
# 進入專案目錄
cd "你的專案路徑"

# 建立新的虛擬環境
python -m venv parking_env
parking_env\Scripts\activate
```

#### 1.2 安裝所需套件
```bash
# 安裝所有必要套件
pip install -r requirements.txt

# 驗證核心套件安裝
python -c "import torch, cv2, flask, numpy, shapely; print('所有核心套件已安裝成功')"
```

#### 1.3 準備模型檔案
確保 `weights/` 資料夾包含：
- `best.pt` - YOLOv7 車輛檢測模型
- `yolov7_plate_0421.pt` - 車牌辨識模型
- `new_pkg.p` - 停車位設定檔案

### 步驟 2: 本地測試系統

#### 2.1 測試 YOLOv7 檢測系統
```bash
# 測試車輛檢測 (使用攝影機)
python detect_yolov7.py --source 0 --weights weights/best.pt

# 測試圖片檔案檢測
python detect_yolov7.py --source "test_image.jpg" --weights weights/best.pt
```

#### 2.2 測試車牌辨識功能
```bash
# 測試車牌辨識
python detect_rec_plate.py --source "platePic" --weights weights/yolov7_plate_0421.pt
```

#### 2.3 啟動 API 服務
```bash
# 在本地啟動 API 服務
python parking_api.py
```

API 會在 `http://localhost:5000` 執行，提供以下端點：
- `GET /` - 服務首頁資訊
- `GET /health` - 健康檢查
- `POST /api/parking/update` - 更新停車位狀態
- `GET /api/parking/status` - 查詢所有停車位
- `GET /api/parking/my_status?plate=車牌` - 查詢個人車位

#### 2.4 測試 API 功能
```bash
# 執行自動化端點測試
python api_test.py
```

### 步驟 3: 整合系統測試

#### 3.1 連接檢測和API系統
在 `detect_yolov7.py` 中已配置 API 連接：

```python
# API 配置 - 可以通過環境變量設置API地址
API_URL = os.environ.get('API_URL', 'https://parking-management-api-lyvg.onrender.com/api/parking/update')
```

#### 3.2 完整流程測試
```bash
# 1. 啟動 API 服務 (終端機 1)
python parking_api.py

# 2. 啟動 YOLOv7 檢測 (終端機 2)
python detect_yolov7.py --source 0

# 3. 測試 API 功能 (終端機 3)
python api_test.py
```

### 步驟 4: 雲端部署 (Render)

#### 4.1 部署前準備

Render 部署所需檔案已準備好：
- `Procfile`: 指定啟動命令
- `.gitignore`: 排除不必要的檔案

#### 4.2 在 Render 建立 PostgreSQL 資料庫

1. 登入 [Render.com](https://render.com)
2. 從左側導航選擇 "PostgreSQL"
3. 點擊 "New PostgreSQL" 建立新資料庫
4. 配置設定：
   ```
   Name: parking-db
   Database: parking
   User: parking_user
   ```
5. 建立後，記下提供的 "Internal Database URL" 和 "External Database URL"

#### 4.3 部署到 Render

1. 在 Render 控制台中選擇 "Web Services"
2. 點擊 "New Web Service"
3. 連接你的 GitHub 專案
4. 配置部署設定：
   ```
   Name: parking-management-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn parking_api:app
   ```
5. 在 "Environment Variables" 設定中，添加：
   ```
   DATABASE_URL: [從上一步複製的 Internal Database URL]
   ```
6. 點擊 "Create Web Service" 啟動部署

#### 4.4 測試雲端部署
```bash
# 修改測試檔案中的 API 基礎地址
# 將 API_BASE_URL 環境變數設定為你的 Render 網址
export API_BASE_URL="https://你的應用.onrender.com/api"
python api_test.py
```

### 步驟 5: 樹莓派設置

#### 5.1 樹莓派配置
在樹莓派上修改 `detect_yolov7.py`，設定雲端 API：

```python
# 設定 API 網址
API_URL = "https://你的應用.onrender.com/api/parking/update"
```

#### 5.2 設定自動啟動
建立 `start_detection.sh`：
```bash
#!/bin/bash
cd /home/pi/parking_project
source venv/bin/activate
python detect_yolov7.py --source 0
```

設定為開機自動執行：
```bash
# 編輯 crontab
crontab -e

# 加入以下行
@reboot /home/pi/parking_project/start_detection.sh
```

---

## API 使用說明

### 基礎URL
- **本地開發**: `http://localhost:5000/api`
- **生產環境**: `https://parking-management-api-lyvg.onrender.com/api`

### 主要端點

#### 1. 更新停車位狀態 (樹莓派使用)
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
  "started_at": "2023-05-24 14:00:00",
  "duration_minutes": 85,
  "fee": 20
}
```

## 資料庫說明

### PostgreSQL 資料庫架構

本系統使用 PostgreSQL 資料庫存儲停車資訊，主要資料表結構：

```sql
CREATE TABLE parking_spaces (
    id INTEGER PRIMARY KEY,
    is_occupied BOOLEAN DEFAULT FALSE,
    license_plate_number VARCHAR(20),
    license_plate_color VARCHAR(20),
    parking_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 資料庫連接設定

- 系統透過環境變數 `DATABASE_URL` 自動連接到 Render 提供的 PostgreSQL 資料庫
- 如果環境變數不存在，系統會自動切換到記憶體模式運作
- 記憶體模式適合本地開發和測試

### 監控資料庫狀態

可通過健康檢查端點監控資料庫連接狀態：

```http
GET /health
```

回應範例：
```json
{
  "status": "healthy",
  "timestamp": "2023-05-24T14:00:00",
  "uptime": "running",
  "database": "connected"
}
```

## 進階開發建議

### 1. 資料庫擴展
- 增加 PostgreSQL 容量
- 設計歷史記錄表
- 建立用戶認證

### 2. 前端開發
- React.js 管理介面
- 即時車位顯示
- 手機 App 整合

### 3. 功能拓展
- 車牌預約功能
- 長期停車折扣
- 多種付款方式

---

## 問題排解

如果遇到問題，請檢查：
1. 環境變數設定是否正確 (`DATABASE_URL` 和 `API_URL`)
2. 所有依賴套件是否已安裝
3. 模型檔案是否已放置於正確位置
4. 確保網路連接能夠訪問 API 服務
5. Render 服務狀態是否正常運作

### 常見問題解決方案

#### 資料庫連接錯誤
```
? 資料庫連接失敗: 連接被拒絕
```
解決方案：檢查 `DATABASE_URL` 是否正確，或確認 Render PostgreSQL 服務是否在運行中

#### API 連接問題
```
? 無法連接到 API 服務
```
解決方案：檢查網路連接，確認 API 服務網址是否正確，Render 服務是否啟動

#### 車牌辨識問題
```
車牌辨識錯誤: [Error]
```
解決方案：確認 `weights/` 資料夾中的模型檔案是否完整，檢查攝影機連接和光線條件

---

## 授權說明

本專案僅供學習與研究使用，請勿用於商業目的。

---

*最後更新: 2023年5月24日*