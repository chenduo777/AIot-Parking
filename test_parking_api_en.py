#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import os
import sys
from datetime import datetime

# API base URL
if len(sys.argv) > 1:
    BASE_URL = sys.argv[1]
else:
    BASE_URL = os.environ.get('API_URL', 'https://parking-management-api-lyvg.onrender.com/api')

# Secret key for reset (建議設為環境變數或從 CLI 傳入)
RESET_SECRET = os.environ.get('RESET_SECRET', 'my_dev_key')

def reset_parking_data():
    """Send reset request to the API"""
    print(f"Sending reset request to {BASE_URL}/reset...\n")

    try:
        response = requests.post(f"{BASE_URL}/reset", json={"secret_key": RESET_SECRET})
        if response.status_code == 200:
            print("? Parking data has been reset.\n")
            return True
        else:
            print(f"? Reset failed (Status code: {response.status_code})")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"? Connection error during reset: {e}")
        return False

def get_parking_status():
    """Get and display parking status"""
    print(f"Getting parking information from {BASE_URL}/parking/status...\n")

    try:
        response = requests.get(f"{BASE_URL}/parking/status")

        if response.status_code == 200:
            parking_data = response.json()

            print("=" * 50)
            print("Parking ID  Status     License Plate")
            print("-" * 50)

            for space in parking_data:
                status = "Occupied" if space['is_occupied'] else "Available"
                plate = space['plate_number'] if space['plate_number'] else "None"
                print(f"{space['id']}          {status}    {plate}")

            print("=" * 50)

            occupied_count = sum(1 for space in parking_data if space['is_occupied'])
            available_count = len(parking_data) - occupied_count

            print("\nParking Statistics:")
            print(f"Total spaces: {len(parking_data)}")
            print(f"Occupied: {occupied_count}")
            print(f"Available: {available_count}")
            print(f"Updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\nRaw JSON data:")
            print(json.dumps(parking_data, indent=2))

            return True
        else:
            print(f"Error: Unable to get parking information (Status code: {response.status_code})")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API service")
        return False
    except Exception as e:
        print(f"Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("Parking Reset & Status Test Tool")
    print("=" * 50)

    if reset_parking_data():
        get_parking_status()
