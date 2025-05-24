import argparse
import time
from pathlib import Path
import os
import re
import pyodbc

import cv2
import torch
import torch.backends.cudnn as cudnn

#---------samadd----------------
import numpy as np
from shapely.geometry import Polygon as shapely_poly
import pickle
import subprocess
import datetime
#---------samadd----------------

from numpy import random

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel




webcam_2 = 0
F_subprocess = 1

class Car:
    def __init__(self, number_plate, color, has_parking):
        self.number_plate = number_plate
        self.color = color
        self.has_parking = has_parking

cars = [None] * 4
# 初始化每個 Car 物件
cars[0] = Car("None", "None", False)
cars[1] = Car("None", "None", False)
cars[2] = Car("None", "None", False)
cars[3] = Car("None", "None", False)

hasCar = [False, False, False, False]


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

# 連接 SQL Server 資料庫

conn = pyodbc.connect(
    driver='{ODBC Driver 18 for SQL Server}',
    server='192.168.193.146',
    database='JackyMSSQL',
    user='yolo',
    password='1qazXSW@',
    as_dict=True,
    charset='UTF-8',  # 指定字符集为 UTF-8
    sslmode='disable',   # 禁用 SSL 验证
    TrustServerCertificate='yes'  # 信任服务器提供的证书
)

# 創建 cursor 物件
cursor = conn.cursor()

def sendData():    
# 循環處理每個識別結果
    for recognition_result in recognition_results:
        last_update_query = f"""
        SELECT LicensePlateNumber FROM ParkingSpaces
        WHERE ID = {recognition_result['ID']};
        """
        cursor.execute(last_update_query)
       
        row = cursor.fetchone()
        if row and row[0] != recognition_result['LicensePlateNumber']:
            # 获取当前时间
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 建立 SQL UPDATE 指令，同时更新停车时间
            update_query = f"""
                UPDATE ParkingSpaces
                SET 
                    IsOccupied = {int(recognition_result['IsOccupied'])},
                    LicensePlateColor = '{recognition_result['LicensePlateColor']}',
                    LicensePlateNumber = '{recognition_result['LicensePlateNumber']}',
                    ParkingTime = {'NULL' if recognition_result['LicensePlateNumber'] == 'None' else f"'{current_time}'"}
                WHERE ID = {recognition_result['ID']};
            """
            # 執行 SQL UPDATE 操作
            cursor.execute(update_query)
            conn.commit()

'''
def hasCar_changed():
    global cars ,hasCar
    if any(cars[i].has_parking != hasCar[i] for i in range(4)):
        for i in range(4):
            hasCar[i] = cars[i].has_parking
        return True
    return False
'''
def hasCar_changed():
    global cars, hasCar
    for i in range(4):
        if cars[i].has_parking != hasCar[i]:  # 如果狀態改變
            if cars[i].has_parking:
                hasCar[i] = cars[i].has_parking
                return True
            else:
                hasCar[i] = cars[i].has_parking
                return False
    return False



def normalize_license_plate(plate):
    match = re.match(r'([A-Za-z]+)(\d+)', plate)
    if match:
        return f'{match.group(1)}-{match.group(2)}'
    else:
        return plate

def convert_to_boxes(coordinates):
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

def compute_parking_moto(parked_car_boxes_poly, motorcycles_boxes_poly, number_plates_boxes_poly,cars,imgs):
    for i, pol1 in enumerate(parked_car_boxes_poly):
        cars[i].has_parking = False 
        for pol2 in motorcycles_boxes_poly:
            polygon_intersection = pol1.intersection(pol2).area
            polygon_union = pol1.union(pol2).area
            IOU = polygon_intersection / polygon_union
            if IOU > 0.2:
                cars[i].has_parking = True   
                for pol3 in number_plates_boxes_poly:
                    poly_intersection = pol2.intersection(pol3).area
                    poly_union = pol2.union(pol3).area
                    IOU_2 = poly_intersection / poly_union
                    if IOU_2 > 0.01 and (cars[i].has_parking != hasCar[i]):
                        x_min, y_min, x_max, y_max = pol3.bounds
                        if webcam_2:
                            license_plate_image = imgs[int(y_min):int(y_max), int(x_min):int(x_max)]                            
                        else:
                            license_plate_image = imgs[0][int(y_min):int(y_max), int(x_min):int(x_max)]# use webcam
                        cv2.imwrite(os.path.join("platePic", str(i)+".jpg"), license_plate_image)


def shape_poly(boxes):
    x1, y1, x2, y2 = boxes
    pol2_xy = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    polygon2_shape = shapely_poly(pol2_xy)
    return polygon2_shape

def clear_images_in_folder(folder_path):
    # 檢查資料夾是否存在
    if not os.path.exists(folder_path):
        return
    # 列出資料夾內所有檔案
    files = os.listdir(folder_path)
    # 迭代每個檔案，刪除圖片
    for file in files:
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            os.remove(file_path)

def detect(save_img=False):
    source, weights, view_img, save_txt, imgsz, trace = opt.source, opt.weights, opt.view_img, opt.save_txt, opt.img_size, not opt.no_trace
    #save_img = not opt.nosave and not source.endswith('.txt')  # save inference images
    webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
        ('rtsp://', 'rtmp://', 'http://', 'https://'))
    
    number_plates_index = 0
    motorcycles_index = 1
    clear_images_in_folder("platePic")
    #---------samadd----------------
    # Load parked_car_boxes
    if webcam_2:
        regions = "weights/new_pkg.p"                    
    else:
        regions = "regions.p"     
    
    with open(regions, 'rb') as f:
        parked_car_boxes = pickle.load(f)
    # 轉換成方框格式
    parked_car_boxes_poly = []
    boxes = convert_to_boxes(parked_car_boxes)
    for box in boxes:
        polygon = shape_poly(box)
        parked_car_boxes_poly.append(polygon)

    #---------samadd----------------
    # Initialize
    set_logging()
    device = select_device(opt.device)
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size

    trace = False
    if trace:
        model = TracedModel(model, device, opt.img_size)

    if half:
        model.half()  # to FP16

    if webcam:
        #view_img = check_imshow()
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz, stride=stride)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride)

    # Get names and colors
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
    
    # Run inference
    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once
    old_img_w = old_img_h = imgsz
    old_img_b = 1
    
    sendData()

    t0 = time.time()
    for path, img, im0s, vid_cap in dataset:
        t1 = time_synchronized()
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Warmup
        if device.type != 'cpu' and (old_img_b != img.shape[0] or old_img_h != img.shape[2] or old_img_w != img.shape[3]):
            old_img_b = img.shape[0]
            old_img_h = img.shape[2]
            old_img_w = img.shape[3]
            for i in range(3):
                model(img, augment=opt.augment)[0]

        # Inference
        
        with torch.no_grad():   # Calculating gradients would cause a GPU memory leak
            pred = model(img, augment=opt.augment)[0]
        #t2 = time_synchronized()

        # Apply NMS
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        #t3 = time_synchronized()

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            if webcam:  # batch_size >= 1
                p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
            else:
                p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            #gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            #for i in range(4):
            #        cars[i].has_parking = False
            
            
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
                
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string
                
                #-----get motorcycles & number_plates boxes-----
                number_plates_boxes = []
                motorcycles_boxes = []
                number_plates_boxes_poly = []
                motorcycles_boxes_poly = []
                for detection in det:
                    box_coordinates = detection[:4]
                    class_index = int(detection[5])
                    # 根據類別索引將座標添加到對應的列表中
                    if class_index == number_plates_index:
                        number_plates_boxes.append(box_coordinates)
                    elif class_index == motorcycles_index:
                        motorcycles_boxes.append(box_coordinates)

                number_plates_boxes = [box.tolist() for box in number_plates_boxes]
                motorcycles_boxes = [box.tolist() for box in motorcycles_boxes]

                for box in number_plates_boxes:
                    polygon = shape_poly(box)
                    number_plates_boxes_poly.append(polygon)

                for box in motorcycles_boxes:
                    polygon = shape_poly(box)
                    motorcycles_boxes_poly.append(polygon)   

                #-----get motorcycles & number_plates boxes-----

                compute_parking_moto(parked_car_boxes_poly,motorcycles_boxes_poly,number_plates_boxes_poly,cars,im0s)
                
                if (cars[0].has_parking or cars[1].has_parking or cars[2].has_parking or cars[3].has_parking) and hasCar_changed():
                    t3 = time_synchronized()
                    process = subprocess.Popen(['python', 'detect_rec_plate.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output, _ = process.communicate()
                    t4 = time_synchronized()
                    clear_images_in_folder("platePic")
                    matches = re.findall(r'\[.*?\]', output.decode(), re.DOTALL)
                    numIDList = []
                    # 输出匹配到的内容
                    for i,match in enumerate(matches):
                        if i == 0:
                            numIDList = eval(match)
                        elif i == 1:
                            numPlateList = eval(match)
                        elif i == 2:
                            colorList = eval(match)   

                    for i in range(len(numIDList)):
                        cars[numIDList[i]].number_plate = numPlateList[i]
                        cars[numIDList[i]].color = colorList[i]
            else:
                for i in range(4):
                    cars[i].has_parking = False

            for i in range(4):
                    if cars[i].has_parking == False:
                        cars[i].number_plate = "None"
                        cars[i].color = "None"

            for i, car in enumerate(cars):
                car.number_plate = normalize_license_plate(car.number_plate)
                print(i,":", car.number_plate, ":", car.color,":", car.has_parking)
                result = next((item for item in recognition_results if item['ID'] == i + 1), None)
                if result:
                # 添加車輛資料到該字典中
                    result['LicensePlateNumber'] = car.number_plate
                    result['LicensePlateColor'] = car.color
                    result['IsOccupied'] = car.has_parking
                # 打印输出        
            sendData()
            print("-----------sendData-----------")  
            t2 = time_synchronized()
            print(f'----{s}Done. ({(1E3 * (t2 - t1)):.1f}ms) detect----')
            
    #print(f'Done. ({time.time() - t0:.3f}s)')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser() 
    parser.add_argument('--weights', nargs='+', type=str, default='weights/best.pt', help='model.pt path(s)')
    #parser.add_argument('--source', type=str, default='pic/det_plate/1222/moto_2_2.jpg', help='source')  # file/folder, 0 for webcam
    parser.add_argument('--source', type=str, default='0', help='source')  # file/folder, 0 for webcam
    parser.add_argument('--img-size', type=int, default= 320 , help='inference size (pixels)')#256
    parser.add_argument('--conf-thres', type=float, default=0.6, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='display results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default='runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--no-trace', action='store_true', help='don`t trace model')
    opt = parser.parse_args()
    print(opt)
    #check_requirements(exclude=('pycocotools', 'thop'))

    
    with torch.no_grad():
        if opt.update:  # update all models (to fix SourceChangeWarning)
            for opt.weights in ['yolov7.pt']:
                detect()
                strip_optimizer(opt.weights)
        else:
            detect()