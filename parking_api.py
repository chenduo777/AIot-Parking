from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 全域變數儲存停車場狀態
parking_data = {}

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
        
        # 尋找車牌對應的停車位
        for space_id, space_info in parking_data.items():
            if space_info['plate_number'] == plate:
                start_time = space_info['started_at']
                current_time = datetime.now()
                
                # 計算停車時間
                duration = current_time - start_time
                duration_minutes = int(duration.total_seconds() / 60)
                
                # 計算費用
                fee = calculate_fee(start_time)
                
                return jsonify({
                    'is_parked': True,
                    'parking_slot': space_id,
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
    # 本地開發時使用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)