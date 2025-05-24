import requests
import json
import time

# API基礎URL
BASE_URL = "http://localhost:5000/api"

def test_parking_update():
    """測試樹莓派上傳停車狀態"""
    print("=== 測試停車狀態更新 ===\n")
    
    # 模擬樹莓派上傳停車狀態
    test_data = [
        {
            "ID": 1,
            "IsOccupied": True,
            "LicensePlateNumber": "ABC-1234"
        },
        {
            "ID": 2,
            "IsOccupied": False,
            "LicensePlateNumber": "None"
        },
        {
            "ID": 3,
            "IsOccupied": True,
            "LicensePlateNumber": "DEF-5678"
        },
        {
            "ID": 4,
            "IsOccupied": False,
            "LicensePlateNumber": "None"
        }
    ]
    
    print("1. 上傳停車狀態...")
    response = requests.post(f"{BASE_URL}/parking/update", json=test_data)
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    return response.status_code == 200

def test_parking_status():
    """測試取得停車場狀態"""
    print("2. 取得停車場狀態...")
    response = requests.get(f"{BASE_URL}/parking/status")
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    return response.json() if response.status_code == 200 else None

def test_my_status():
    """測試查詢特定車牌狀態"""
    print("3. 查詢車牌 ABC-1234 的停車狀態...")
    response = requests.get(f"{BASE_URL}/parking/my_status?plate=ABC-1234")
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    print("4. 查詢不存在的車牌 XYZ-9999...")
    response = requests.get(f"{BASE_URL}/parking/my_status?plate=XYZ-9999")
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")

def test_fee_calculation():
    """測試停車費用計算"""
    print("=== 測試停車費用計算 ===\n")
    
    # 先上傳一個新車輛
    test_data = [
        {
            "ID": 1,
            "IsOccupied": True,
            "LicensePlateNumber": "TEST-0001"
        },
        {
            "ID": 2,
            "IsOccupied": False,
            "LicensePlateNumber": "None"
        },
        {
            "ID": 3,
            "IsOccupied": False,
            "LicensePlateNumber": "None"
        },
        {
            "ID": 4,
            "IsOccupied": False,
            "LicensePlateNumber": "None"
        }
    ]
    
    print("1. 上傳新車輛停車...")
    requests.post(f"{BASE_URL}/parking/update", json=test_data)
    
    print("2. 立即查詢費用（應該是免費）...")
    response = requests.get(f"{BASE_URL}/parking/my_status?plate=TEST-0001")
    if response.status_code == 200:
        data = response.json()
        print(f"停車時間: {data.get('duration_minutes', 0)} 分鐘")
        print(f"費用: ${data.get('fee', 0)}")
    print()

def test_error_cases():
    """測試錯誤情況"""
    print("=== 測試錯誤處理 ===\n")
    
    # 測試無效的更新資料
    print("1. 測試無效的更新資料...")
    invalid_data = [{"ID": 1}]  # 缺少必要欄位
    response = requests.post(f"{BASE_URL}/parking/update", json=invalid_data)
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    # 測試無效的停車位ID
    print("2. 測試無效的停車位ID...")
    invalid_data = [
        {
            "ID": 5,  # 無效ID
            "IsOccupied": True,
            "LicensePlateNumber": "ABC-1234"
        },
        {
            "ID": 2,
            "IsOccupied": False,
            "LicensePlateNumber": "None"
        },
        {
            "ID": 3,
            "IsOccupied": False,
            "LicensePlateNumber": "None"
        },
        {
            "ID": 4,
            "IsOccupied": False,
            "LicensePlateNumber": "None"
        }
    ]
    response = requests.post(f"{BASE_URL}/parking/update", json=invalid_data)
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    # 測試缺少車牌參數
    print("3. 測試缺少車牌參數...")
    response = requests.get(f"{BASE_URL}/parking/my_status")
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")

def main():
    """主測試函數"""
    print("停車場管理API測試開始...\n")
    
    try:
        # 基本功能測試
        if test_parking_update():
            status_data = test_parking_status()
            test_my_status()
            
            # 費用計算測試
            test_fee_calculation()
            
            # 錯誤處理測試
            test_error_cases()
            
            print("✅ 所有測試完成")
        else:
            print("❌ 基本測試失敗")
            
    except requests.exceptions.ConnectionError:
        print("❌ 錯誤: 無法連接到API伺服器")
        print("請確保API伺服器正在運行: python parking_api.py")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()