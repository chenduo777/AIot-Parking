import requests
import json
import time

def test_production_api(base_url):
    """測試正式環境的API"""
    print(f"=== 測試正式環境API: {base_url} ===\n")
    
    try:
        # 1. 測試首頁
        print("1. 測試首頁...")
        response = requests.get(f"{base_url}/")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"錯誤: {response.text}")
        print()
        
        # 2. 測試健康檢查
        print("2. 測試健康檢查...")
        response = requests.get(f"{base_url}/health")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 3. 上傳測試資料
        print("3. 上傳停車狀態...")
        test_data = [
            {"ID": 1, "IsOccupied": True, "LicensePlateNumber": "ABC-1234"},
            {"ID": 2, "IsOccupied": False, "LicensePlateNumber": "None"},
            {"ID": 3, "IsOccupied": True, "LicensePlateNumber": "DEF-5678"},
            {"ID": 4, "IsOccupied": False, "LicensePlateNumber": "None"}
        ]
        
        response = requests.post(f"{base_url}/api/parking/update", json=test_data)
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"錯誤: {response.text}")
        print()
        
        # 4. 查詢停車場狀態
        print("4. 查詢停車場狀態...")
        response = requests.get(f"{base_url}/api/parking/status")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 5. 查詢個人狀態
        print("5. 查詢個人停車狀態...")
        response = requests.get(f"{base_url}/api/parking/my_status?plate=ABC-1234")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 6. 查詢不存在的車牌
        print("6. 查詢不存在的車牌...")
        response = requests.get(f"{base_url}/api/parking/my_status?plate=XYZ-9999")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        print("✅ 測試完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 錯誤: 無法連接到API伺服器")
        print("請檢查網址是否正確，或等待服務啟動完成")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

def main():
    """主函數"""
    print("停車場API測試工具")
    print("=" * 50)
    
    # 讓使用者輸入API網址
    print("請輸入以下選項:")
    print("1. 測試本地服務器 (http://localhost:5000)")
    print("2. 測試Render部署的服務器")
    print("3. 輸入自定義網址")
    
    choice = input("請選擇 (1/2/3): ").strip()
    
    if choice == "1":
        base_url = "http://localhost:5000"
    elif choice == "2":
        app_name = input("請輸入你的Render應用名稱: ").strip()
        base_url = f"https://{app_name}.onrender.com"
    elif choice == "3":
        base_url = input("請輸入完整的API網址 (例: https://yourapp.onrender.com): ").strip()
    else:
        print("無效選擇，使用本地服務器")
        base_url = "http://localhost:5000"
    
    print(f"\n將測試: {base_url}")
    print("-" * 50)
    
    test_production_api(base_url)

if __name__ == "__main__":
    main()