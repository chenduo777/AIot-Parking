from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import json
import os
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 資料庫連接設定
def get_db_connection():
    """取得資料庫連接"""
    try:
        # Render 會自動提供 DATABASE_URL 環境變數
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # 生產環境 (Render)
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        else:
            # 本地開發環境，使用記憶體儲存
            return None
        return conn
    except Exception as e:
        print(f"資料庫連接失敗: {e}")
        return None

# 全域變數儲存停車場狀態 (當無資料庫時使用)
parking_data = {}

def init_database():
    """初始化資料庫表格"""
    conn = get_db_connection()
    if not conn:
        print("使用記憶體儲存模式")
        return
    
    try:
        cursor = conn.cursor()
        # 建立停車場表格
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_spaces (
                id INTEGER PRIMARY KEY,
                is_occupied BOOLEAN DEFAULT FALSE,
                license_plate_number VARCHAR(20),
                license_plate_color VARCHAR(20),
                parking_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 初始化 4 個停車位
        for i in range(1, 5):
            cursor.execute("""
                INSERT INTO parking_spaces (id, is_occupied, license_plate_number, license_plate_color) 
                VALUES (%s, %s, %s, %s) 
                ON CONFLICT (id) DO NOTHING;
            """, (i, False, None, None))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ 資料庫初始化成功")
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")

def calculate_fee(start_time):
    """計算停車費用：前30分鐘免費，每小時$20"""
    if not start_time:
        return 0
    
    current_time = datetime.now()
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('T', ' '))
    
    duration = current_time - start_time
    duration_minutes = int(duration.total_seconds() / 60)
    
    if duration_minutes <= 30:
        return 0
    else:
        # 超過30分鐘的部分，每小時$20
        billable_minutes = duration_minutes - 30
        hours = (billable_minutes + 59) // 60  # 無條件進位到小時
        return hours * 20

@app.route('/', methods=['GET'])
def home():
    """首頁端點"""
    return jsonify({
        'message': '停車場管理API服務',
        'version': '1.0.0',
        'endpoints': [
            'POST /api/parking/update - 更新停車狀態',
            'GET /api/parking/status - 取得停車場狀態',
            'GET /api/parking/my_status?plate=車牌 - 查詢個人停車狀態'
        ],
        'status': 'running',
        'current_time': datetime.now().isoformat(),
        'active_parkings': len(parking_data)
    })

@app.route('/api/parking/update', methods=['POST'])
def update_parking_status():
    """接收樹莓派上傳的停車狀態"""
    try:
        data = request.get_json()
        
        if not data or not isinstance(data, list) or len(data) != 4:
            return jsonify({
                'success': False,
                'error': '請求格式錯誤，需要包含4個停車位的資料'
            }), 400
        
        current_time = datetime.now()
        conn = get_db_connection()
        
        if conn:
            # 使用資料庫
            cursor = conn.cursor()
            
            for space_data in data:
                space_id = space_data.get('ID')
                is_occupied = space_data.get('IsOccupied', False)
                plate_number = space_data.get('LicensePlateNumber', 'None')
                plate_color = space_data.get('LicensePlateColor', 'None')
                
                # 處理車牌號碼
                if plate_number == 'None' or not plate_number:
                    plate_number = None
                if plate_color == 'None' or not plate_color:
                    plate_color = None
                
                # 更新資料庫
                cursor.execute("""
                    UPDATE parking_spaces 
                    SET is_occupied = %s, 
                        license_plate_number = %s,
                        license_plate_color = %s,
                        parking_time = %s,
                        updated_at = %s
                    WHERE id = %s;
                """, (is_occupied, plate_number, plate_color, 
                     current_time if is_occupied else None, current_time, space_id))
            
            conn.commit()
            cursor.close()
            conn.close()
        else:
            # 使用記憶體儲存 (本地開發)
            for space_data in data:
                space_id = space_data.get('ID')
                is_occupied = space_data.get('IsOccupied', False)
                plate_number = space_data.get('LicensePlateNumber', 'None')
                
                # 驗證資料格式
                if space_id not in [1, 2, 3, 4]:
                    return jsonify({
                        'success': False,
                        'error': f'無效的停車位ID: {space_id}'
                    }), 400
                
                # 處理車牌號碼
                if plate_number == 'None' or not plate_number:
                    plate_number = None
                
                # 如果停車位原本是空的，現在有車了
                if space_id not in parking_data and is_occupied and plate_number:
                    parking_data[space_id] = {
                        'plate_number': plate_number,
                        'started_at': current_time,
                        'is_occupied': True
                    }
                # 如果停車位原本有車，現在空了
                elif space_id in parking_data and not is_occupied:
                    del parking_data[space_id]
                # 如果停車位有車且車牌相同，更新狀態
                elif space_id in parking_data and is_occupied and plate_number:
                    parking_data[space_id]['plate_number'] = plate_number
                    parking_data[space_id]['is_occupied'] = True
        
        return jsonify({
            'success': True,
            'message': '停車狀態更新成功',
            'timestamp': current_time.isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'更新失敗: {str(e)}'
        }), 500

@app.route('/api/parking/status', methods=['GET'])
def get_parking_status():
    """取得所有停車位狀態"""
    try:
        conn = get_db_connection()
        
        if conn:
            # 使用資料庫
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parking_spaces ORDER BY id;")
            spaces = cursor.fetchall()
            cursor.close()
            conn.close()
            
            result = []
            for space in spaces:
                result.append({
                    'id': space['id'],
                    'is_occupied': space['is_occupied'],
                    'plate_number': space['license_plate_number']
                })
            return jsonify(result)
        else:
            # 使用記憶體儲存
            result = []
            for space_id in [1, 2, 3, 4]:
                if space_id in parking_data:
                    result.append({
                        'id': space_id,
                        'is_occupied': True,
                        'plate_number': parking_data[space_id]['plate_number']
                    })
                else:
                    result.append({
                        'id': space_id,
                        'is_occupied': False,
                        'plate_number': None
                    })
            return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'查詢失敗: {str(e)}'
        }), 500

@app.route('/api/parking/my_status', methods=['GET'])
def get_my_parking_status():
    """查詢特定車牌的停車狀態"""
    try:
        plate = request.args.get('plate')
        
        if not plate:
            return jsonify({
                'success': False,
                'error': '請提供車牌號碼參數'
            }), 400
        
        conn = get_db_connection()
        
        if conn:
            # 使用資料庫
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parking_spaces WHERE license_plate_number = %s;", (plate,))
            space = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if space:
                start_time = space['parking_time']
                current_time = datetime.now()
                
                # 計算停車時間
                duration = current_time - start_time
                duration_minutes = int(duration.total_seconds() / 60)
                
                # 計算費用
                fee = calculate_fee(start_time)
                
                return jsonify({
                    'is_parked': True,
                    'parking_slot': space['id'],
                    'started_at': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_minutes': duration_minutes,
                    'fee': fee
                })
        
        # 沒有找到車牌
        return jsonify({
            'is_parked': False,
            'message': '您的車目前未停在停車場內'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'查詢失敗: {str(e)}'
        }), 500

# 健康檢查端點
@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點，Render會用這個檢查服務狀態"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': 'running'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'API端點不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '內部伺服器錯誤'
    }), 500

if __name__ == '__main__':
    # 初始化資料庫
    init_database()
    
    # 本地開發時使用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)