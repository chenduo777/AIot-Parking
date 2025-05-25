# -*- coding: utf-8 -*-
import argparse
import time
import os
import re
import pyodbc
import json
import threading
import queue
import sys
import cv2
import torch
import torch.backends.cudnn as cudnn
import numpy as np
import pickle
import subprocess
from pathlib import Path
from numpy import random
from datetime import datetime

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, non_max_suppression, scale_coords, set_logging
from utils.torch_utils import select_device, time_synchronized, TracedModel

# Import custom tools
from utils.parking_utils import Car, normalize_license_plate, convert_to_boxes, shape_poly, clear_images_in_folder, send_parking_data

# API configuration - can be changed via environment variables
API_URL = os.environ.get('API_URL', 'http://localhost:5000/api/parking/update')
print(f"Using API URL: {API_URL}")

# SQL Server connection string - should be configured via environment variables in production
SQL_CONNECTION_STRING = os.environ.get('SQL_CONNECTION_STRING', 'DRIVER={SQL Server};SERVER=localhost;DATABASE=ParkingDB;UID=sa;PWD=YourPassword')

# Initialize car objects for each parking space
cars = [Car() for _ in range(4)]
has_car = [False, False, False, False]

recognition_results = [
    {
        'ID': 1,
        'IsOccupied': False,
        'LicensePlateColor': 'None',
        'LicensePlateNumber': 'None'
    },
    {
        'ID': 2,
        'IsOccupied': False,
        'LicensePlateColor': 'None',
        'LicensePlateNumber': 'None'
    },
    {
        'ID': 3,
        'IsOccupied': False,
        'LicensePlateColor': 'None',
        'LicensePlateNumber': 'None'
    },
    {
        'ID': 4,
        'IsOccupied': False,
        'LicensePlateColor': 'None',
        'LicensePlateNumber': 'None'
    }
]

def store_parking_data_to_db():
    """Store parking data to SQL Server database"""
    try:
        conn = pyodbc.connect(SQL_CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Create parking spaces table if it doesn't exist
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ParkingSpaces')
            BEGIN
                CREATE TABLE ParkingSpaces (
                    ID INT PRIMARY KEY,
                    IsOccupied BIT,
                    LicensePlateNumber NVARCHAR(20),
                    LicensePlateColor NVARCHAR(20),
                    LastUpdated DATETIME
                )
            END
        """)
        conn.commit()
        
        # Insert or update parking data
        for result in recognition_results:
            cursor.execute("""
                MERGE INTO ParkingSpaces AS target
                USING (SELECT ? AS ID, ? AS IsOccupied, ? AS LicensePlateNumber, ? AS LicensePlateColor) AS source
                ON target.ID = source.ID
                WHEN MATCHED THEN
                    UPDATE SET IsOccupied = source.IsOccupied, 
                                LicensePlateNumber = source.LicensePlateNumber,
                                LicensePlateColor = source.LicensePlateColor,
                                LastUpdated = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (ID, IsOccupied, LicensePlateNumber, LicensePlateColor, LastUpdated)
                    VALUES (source.ID, source.IsOccupied, source.LicensePlateNumber, source.LicensePlateColor, GETDATE());
            """, 
            result['ID'], 
            1 if result['IsOccupied'] else 0, 
            result['LicensePlateNumber'],
            result['LicensePlateColor'])
        
        conn.commit()
        print("? Database updated successfully")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"? Database error: {e}")
        # Fallback to API
        send_parking_data(API_URL, recognition_results)

def detect(opt):
    source, weights, img_size = opt.source, opt.weights, opt.img_size
    webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
        ('rtsp://', 'rtmp://', 'http://', 'https://'))

    # Load YOLOv7 model
    device = select_device(opt.device)
    model = attempt_load(weights, map_location=device)
    stride = int(model.stride.max())
    img_size = check_img_size(img_size, s=stride)
    
    # Setup camera
    if webcam:
        dataset = LoadStreams(source, img_size=img_size, stride=stride)
    else:
        dataset = LoadImages(source, img_size=img_size, stride=stride)
    
    # Get model info
    names = model.module.names if hasattr(model, 'module') else model.names
    
    # Load parking spaces configuration
    with open(opt.parking_config, 'rb') as f:
        parking_spaces = pickle.load(f)
    
    # Convert to polygon format for intersection calculations
    parking_spaces_poly = []
    boxes = convert_to_boxes(parking_spaces)
    for box in boxes:
        polygon = shape_poly(box)
        parking_spaces_poly.append(polygon)
    
    # Setup directory for license plate images
    os.makedirs("platePic", exist_ok=True)
    clear_images_in_folder("platePic")
    
    # Main detection loop
    t0 = time.time()
    for path, img, im0s, vid_cap in dataset:
        img = torch.from_numpy(img).to(device)
        img = img.float()  # Convert to float32
        img /= 255.0  # Normalize 0-255 to 0.0-1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)
        
        # Run inference
        pred = model(img, augment=opt.augment)[0]
        
        # Apply NMS
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        
        # Process detections
        for i, det in enumerate(pred):
            if webcam:
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
            else:
                p, im0, frame = path, im0s, getattr(dataset, 'frame', 0)
            
            # Process vehicle and license plate detections
            # [Implementation for detection processing]
            
            # Update parking status
            # [Implementation for updating status]
            
            # Display status
            for i, car in enumerate(cars):
                print(f"Space {i+1}: {'Occupied' if car.has_parking else 'Empty'} {car.number_plate}")
                # Update recognition results
                result = next((item for item in recognition_results if item['ID'] == i + 1), None)
                if result:
                    result['IsOccupied'] = car.has_parking
                    result['LicensePlateNumber'] = car.number_plate
                    result['LicensePlateColor'] = car.color
            
            # Save/send data
            if opt.use_database:
                store_parking_data_to_db()
            else:
                send_parking_data(API_URL, recognition_results)
            
            print(f"Data sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
    print(f"Detection completed in {time.time() - t0:.2f} seconds")

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str, default='weights/best.pt', help='model.pt path')
    parser.add_argument('--source', type=str, default='0', help='source (0 for webcam)')
    parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--parking-config', type=str, default='regions.p', help='parking spaces configuration file')
    parser.add_argument('--use-database', action='store_true', help='use SQL Server database instead of API')
    return parser.parse_args()

if __name__ == '__main__':
    # Parse command line arguments
    opt = parse_arguments()
    print(opt)
    
    # Initialize logging
    set_logging()
    
    # Run detection
    with torch.no_grad():
        detect(opt)