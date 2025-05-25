# -*- coding: utf-8 -*-
import requests
import json
import time
import os

# API base URL - can be set via environment variable
BASE_URL = os.environ.get('API_BASE_URL', 'https://parking-management-api-lyvg.onrender.com/api')
print(f"Using API base URL: {BASE_URL}")

def test_parking_update():
    """Test sending parking status data"""
    print("=== Testing Parking Status Update ===\n")
    
    # Prepare test data
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
    
    print("1. Uploading parking status...")
    response = requests.post(f"{BASE_URL}/parking/update", json=test_data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    return response.status_code == 200

def test_parking_status():
    """Test retrieving parking lot status"""
    print("2. Getting parking lot status...")
    response = requests.get(f"{BASE_URL}/parking/status")
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    return response.json() if response.status_code == 200 else None

def test_my_status():
    """Test individual parking status"""
    print("3. Checking license plate ABC-1234 status...")
    response = requests.get(f"{BASE_URL}/parking/my_status?plate=ABC-1234")
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    print("4. Checking non-existent license plate XYZ-9999...")
    response = requests.get(f"{BASE_URL}/parking/my_status?plate=XYZ-9999")
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_fee_calculation():
    """Test parking fee calculation"""
    print("=== Testing Fee Calculation ===\n")
    
    # Upload test plate data
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
    
    print("1. Uploading test license plate...")
    requests.post(f"{BASE_URL}/parking/update", json=test_data)
    
    print("2. Checking fee (should be free within 30 minutes)...")
    response = requests.get(f"{BASE_URL}/parking/my_status?plate=TEST-0001")
    if response.status_code == 200:
        data = response.json()
        print(f"Parking duration: {data.get('duration_minutes', 0)} minutes")
        print(f"Fee: ${data.get('fee', 0)}")
    print()

def test_error_cases():
    """Test error handling"""
    print("=== Testing Error Scenarios ===\n")
    
    # Test invalid update data
    print("1. Testing invalid update data...")
    invalid_data = [{"ID": 1}]  # Missing required fields
    response = requests.post(f"{BASE_URL}/parking/update", json=invalid_data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test invalid parking space ID
    print("2. Testing invalid parking space ID...")
    invalid_data = [
        {
            "ID": 5,  # Invalid ID
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
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test missing plate parameter
    print("3. Testing missing plate parameter...")
    response = requests.get(f"{BASE_URL}/parking/my_status")
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def main():
    """Main test function"""
    print("Parking Management API Test Starting...\n")
    
    try:
        # Run basic tests
        if test_parking_update():
            status_data = test_parking_status()
            test_my_status()
            
            # Fee calculation test
            test_fee_calculation()
            
            # Error scenario tests
            test_error_cases()
            
            print("Test completed successfully")
        else:
            print("Basic test failed")
            
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API service")
        print("Please ensure API service is running: python parking_api.py")
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    main()