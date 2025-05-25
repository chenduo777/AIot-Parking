# -*- coding: utf-8 -*-
import os
import re
import cv2
import numpy as np
import requests
from shapely.geometry import Polygon as shapely_poly

# API 配置 - 可以通過環境變量設置API地址
API_URL = os.environ.get('API_URL', 'https://parking-management-api-lyvg.onrender.com/api/parking/update')

class Car:
    """Class representing a car in a parking space"""
    def __init__(self):
        self.has_parking = False
        self.number_plate = "None"
        self.color = "None"

def detect_color(p):
    """Detect the color of a license plate"""
    try:
        img = cv2.imread(str(p))
        if img is None:
            return "Unknown"
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Get average hue value
        h_avg = np.average(h)
        s_avg = np.average(s)
        
        # Color determination based on HSV values
        if s_avg < 50:  # Low saturation usually means white or black
            v_avg = np.average(v)
            if v_avg > 150:
                return "White"
            else:
                return "Black"
        elif 0 <= h_avg <= 15 or 165 <= h_avg <= 180:
            return "Red"
        elif 15 < h_avg <= 25:
            return "Orange"
        elif 25 < h_avg <= 35:
            return "Yellow"
        elif 35 < h_avg <= 85:
            return "Green"
        elif 85 < h_avg <= 125:
            return "Blue"
        elif 125 < h_avg <= 165:
            return "Purple"
        else:
            return "Unknown"
    except Exception as e:
        print(f"Color detection error: {e}")
        return "Unknown"

def clear_images_in_folder(folder_path):
    """Clear all image files in the specified folder"""
    try:
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    os.remove(file_path)
    except Exception as e:
        print(f"Error clearing folder {folder_path}: {e}")

def convert_to_boxes(parked_car_boxes):
    """Convert parking space coordinates to boxes format"""
    boxes = []
    for box in parked_car_boxes:
        x1, y1 = box[0][0], box[0][1]
        x2, y2 = box[1][0], box[1][1]
        x3, y3 = box[2][0], box[2][1]
        x4, y4 = box[3][0], box[3][1]
        
        xmin = min(x1, x2, x3, x4)
        ymin = min(y1, y2, y3, y4)
        xmax = max(x1, x2, x3, x4)
        ymax = max(y1, y2, y3, y4)
        
        boxes.append([xmin, ymin, xmax, ymax])
    return boxes

def shape_poly(box):
    """Convert box coordinates to shapely polygon"""
    if len(box) == 4:
        # If box is [xmin, ymin, xmax, ymax] format
        return shapely_poly([
            (box[0], box[1]),
            (box[2], box[1]),
            (box[2], box[3]),
            (box[0], box[3])
        ])
    else:
        # If box is a list of points
        return shapely_poly([(point[0], point[1]) for point in box])

def normalize_license_plate(plate_text):
    """Normalize license plate text format"""
    if plate_text == "None" or not plate_text:
        return "None"
    
    # Remove any non-alphanumeric characters except hyphen
    plate_text = re.sub(r'[^A-Z0-9\-]', '', plate_text.upper())
    
    # Check if plate contains both letters and numbers
    has_letters = bool(re.search(r'[A-Z]', plate_text))
    has_numbers = bool(re.search(r'[0-9]', plate_text))
    
    if not has_letters or not has_numbers:
        return "None"  # Invalid plate
    
    # Format as XXX-1234 if not already formatted
    if "-" not in plate_text and len(plate_text) >= 4:
        letters = ""
        numbers = ""
        
        # Extract letters and numbers
        for char in plate_text:
            if char.isalpha():
                letters += char
            elif char.isdigit():
                numbers += char
        
        # Format as XXX-1234
        if letters and numbers:
            return f"{letters[:3]}-{numbers[:4]}"
    
    return plate_text

def send_parking_data(api_url, recognition_results):
    """Send parking data to API endpoint"""
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            api_url,
            json=recognition_results,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("? Data sent successfully")
            return True
        else:
            print(f"? Failed to send data: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("? Cannot connect to API service")
        return False
    except requests.exceptions.Timeout:
        print("? API request timeout")
        return False
    except Exception as e:
        print(f"? Error sending data: {e}")
        return False 