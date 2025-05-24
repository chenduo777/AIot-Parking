import argparse
import time
import os
import re
import pyodbc
import cv2
import torch
import torch.backends.cudnn as cudnn
import numpy as np
from shapely.geometry import Polygon as shapely_poly
import pickle
import subprocess
import datetime
from pathlib import Path
from numpy import random

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, non_max_suppression, scale_coords, set_logging
from utils.torch_utils import select_device, time_synchronized, TracedModel

class ParkingDetector:
    def __init__(self, webcam_source=0, weights_path='weights/best.pt', plate_weights='weights/yolov7_plate_0421.pt'):
        self.webcam_source = webcam_source
        self.weights_path = weights_path
        self.plate_weights = plate_weights
        self.webcam_2 = 0
        self.device = select_device('')
        self.half = self.device.type != 'cpu'
        
        # 初始化停車位狀態
        self.cars = [self.Car("None", "None", False) for _ in range(4)]
        self.hasCar = [False, False, False, False]
        
        # 載入停車位區域
        regions_file = "weights/new_pkg.p" if self.webcam_2 else "regions.p"
        with open(regions_file, 'rb') as f:
            parked_car_boxes = pickle.load(f)
        
        self.parked_car_boxes_poly = []
        boxes = self._convert_to_boxes(parked_car_boxes)
        for box in boxes:
            polygon = self._shape_poly(box)
            self.parked_car_boxes_poly.append(polygon)
        
        # 載入模型
        self._load_model()
        
        # 初始化攝影機
        self.cap = cv2.VideoCapture(self.webcam_source)
        if not self.cap.isOpened():
            raise RuntimeError("無法開啟攝影機")
        
        # 建立platePic資料夾
        os.makedirs("platePic", exist_ok=True)
    
    class Car:
        def __init__(self, number_plate, color, has_parking):
            self.number_plate = number_plate
            self.color = color
            self.has_parking = has_parking
    
    def _load_model(self):
        """載入YOLO模型"""
        set_logging()
        self.model = attempt_load(self.weights_path, map_location=self.device)
        self.stride = int(self.model.stride.max())
        self.imgsz = 320
        self.imgsz = check_img_size(self.imgsz, s=self.stride)
        
        if self.half:
            self.model.half()
        
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        
        # 熱身
        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, self.imgsz, self.imgsz).to(self.device).type_as(next(self.model.parameters())))
    
    def _convert_to_boxes(self, coordinates):
        """將座標轉換為邊界框"""
        boxes = []
        for coords in coordinates:
            x_values = [point[0] for point in coords]
            y_values = [point[1] for point in coords]
            x1 = min(x_values)
            y1 = min(y_values)
            x2 = max(x_values)
            y2 = max(y_values)
            boxes.append([x1, y1, x2, y2])
        return boxes
    
    def _shape_poly(self, boxes):
        """建立多邊形"""
        x1, y1, x2, y2 = boxes
        pol2_xy = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        polygon2_shape = shapely_poly(pol2_xy)
        return polygon2_shape
    
    def _clear_images_in_folder(self, folder_path):
        """清空資料夾中的圖片"""
        if not os.path.exists(folder_path):
            return
        files = os.listdir(folder_path)
        for file in files:
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                os.remove(file_path)
    
    def _normalize_license_plate(self, plate):
        """正規化車牌號碼"""
        match = re.match(r'([A-Za-z]+)(\d+)', plate)
        if match:
            return f'{match.group(1)}-{match.group(2)}'
        else:
            return plate
    
    def _compute_parking_moto(self, motorcycles_boxes_poly, number_plates_boxes_poly, im0):
        """計算停車狀態"""
        for i, pol1 in enumerate(self.parked_car_boxes_poly):
            self.cars[i].has_parking = False 
            for pol2 in motorcycles_boxes_poly:
                polygon_intersection = pol1.intersection(pol2).area
                polygon_union = pol1.union(pol2).area
                if polygon_union > 0:
                    IOU = polygon_intersection / polygon_union
                    if IOU > 0.2:
                        self.cars[i].has_parking = True   
                        for pol3 in number_plates_boxes_poly:
                            poly_intersection = pol2.intersection(pol3).area
                            poly_union = pol2.union(pol3).area
                            if poly_union > 0:
                                IOU_2 = poly_intersection / poly_union
                                if IOU_2 > 0.01 and (self.cars[i].has_parking != self.hasCar[i]):
                                    x_min, y_min, x_max, y_max = pol3.bounds
                                    license_plate_image = im0[int(y_min):int(y_max), int(x_min):int(x_max)]
                                    cv2.imwrite(os.path.join("platePic", str(i)+".jpg"), license_plate_image)
    
    def _hasCar_changed(self):
        """檢查停車狀態是否改變"""
        for i in range(4):
            if self.cars[i].has_parking != self.hasCar[i]:
                if self.cars[i].has_parking:
                    self.hasCar[i] = self.cars[i].has_parking
                    return True
                else:
                    self.hasCar[i] = self.cars[i].has_parking
                    return False
        return False
    
    def _run_plate_recognition(self):
        """執行車牌辨識"""
        try:
            process = subprocess.Popen(['python', 'detect_rec_plate.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     cwd=os.getcwd())
            output, _ = process.communicate()
            self._clear_images_in_folder("platePic")
            
            matches = re.findall(r'\[.*?\]', output.decode(), re.DOTALL)
            if len(matches) >= 3:
                numIDList = eval(matches[0])
                numPlateList = eval(matches[1])
                colorList = eval(matches[2])
                
                for i in range(len(numIDList)):
                    if numIDList[i] < 4:  # 確保索引有效
                        self.cars[numIDList[i]].number_plate = numPlateList[i]
                        self.cars[numIDList[i]].color = colorList[i]
        except Exception as e:
            print(f"車牌辨識錯誤: {e}")
    
    def detect_once(self):
        """執行一次檢測並回傳結果"""
        ret, im0 = self.cap.read()
        if not ret:
            return None
        
        # 預處理圖像
        img = cv2.resize(im0, (self.imgsz, self.imgsz))
        img = img.transpose((2, 0, 1))  # HWC to CHW
        img = np.ascontiguousarray(img)
        
        img = torch.from_numpy(img).to(self.device)
        img = img.half() if self.half else img.float()
        img /= 255.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)
        
        # 推論
        with torch.no_grad():
            pred = self.model(img, augment=False)[0]
        
        # NMS
        pred = non_max_suppression(pred, 0.6, 0.45, classes=None, agnostic=False)
        
        # 處理檢測結果
        number_plates_boxes_poly = []
        motorcycles_boxes_poly = []
        
        for det in pred:
            if len(det):
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
                
                for *xyxy, conf, cls in det:
                    box = [float(x) for x in xyxy]
                    polygon = self._shape_poly(box)
                    
                    if int(cls) == 0:  # number_plates
                        number_plates_boxes_poly.append(polygon)
                    elif int(cls) == 1:  # motorcycles
                        motorcycles_boxes_poly.append(polygon)
        
        # 計算停車狀態
        self._compute_parking_moto(motorcycles_boxes_poly, number_plates_boxes_poly, im0)
        
        # 檢查是否需要車牌辨識
        if any(car.has_parking for car in self.cars) and self._hasCar_changed():
            self._run_plate_recognition()
        
        # 更新無車位的狀態
        for i in range(4):
            if not self.cars[i].has_parking:
                self.cars[i].number_plate = "None"
                self.cars[i].color = "None"
        
        # 正規化車牌號碼並準備結果
        results = []
        for i, car in enumerate(self.cars):
            car.number_plate = self._normalize_license_plate(car.number_plate)
            results.append({
                'ID': i + 1,
                'IsOccupied': car.has_parking,
                'LicensePlateColor': car.color,
                'LicensePlateNumber': car.number_plate
            })
        
        return results
    
    def cleanup(self):
        """清理資源"""
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        self._clear_images_in_folder("platePic")