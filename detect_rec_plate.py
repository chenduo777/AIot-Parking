import argparse
import time
import os
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.backends.cudnn as cudnn
from numpy import random

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel

list = []

def detect(save_img=False):
    
    source, weights, view_img, save_txt, imgsz, trace = opt.source, opt.weights, opt.view_img, opt.save_txt, opt.img_size, not opt.no_trace
    save_img = not opt.nosave and not source.endswith('.txt')  # save inference images
    # Directories
    
    # Initialize
    set_logging()
    device = select_device(opt.device)
    half = device.type != 'cpu'  # half precision only supported on CUDA
    
    t3 = time_synchronized()
    # Load model 1.8s
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size
    t4 = time_synchronized()
    print(f'----Done. ({(1E3 * (t4 - t3)):.1f}ms) TIME----')

    trace = False
    #opt.augment = False
    if trace:
        model = TracedModel(model, device, opt.img_size)

    if half:
        model.half()  # to FP16
    
    # Set Dataloader
    dataset = LoadImages(source, img_size=imgsz, stride=stride)

    # Get names and colors
    names = model.names
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
    
    # Run inference
    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once
    old_img_w = old_img_h = imgsz
    old_img_b = 1
    numberList = []
    plateList = []
    colorList = []
    
    for path, img, im0s, vid_cap in dataset:

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
        t1 = time_synchronized()
        with torch.no_grad():   # Calculating gradients would cause a GPU memory leak
            pred = model(img, augment=opt.augment)[0]
        t2 = time_synchronized()
        # Apply NMS
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        t3 = time_synchronized()

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)
 
            p = Path(p)  # to Path

            if len(det):
                
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                # Write results
                sorted_indices = torch.argsort(det[:, 0], descending=True)# 使用 torch.sort() 对第1列进行排序，并获取由左至右的順序
                sorted_tensor = det[sorted_indices]# 使用排序后的索引重新排列原始张量


                for *xyxy, conf, cls in reversed(sorted_tensor):
                    label = f'{names[int(cls)]} {conf:.2f}'
                    list.append(names[int(cls)])#每次辨識的字符
                    plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=1)
            
            print(f'{s}Done. ({(1E3 * (t2 - t1)):.1f}ms) Inference, ({(1E3 * (t3 - t2)):.1f}ms) NMS')
            
            color_plate = color_Range(p)#辨識顏色            
            Str = "".join(list)#列表轉換為字串
            #print(Str+" "+color_plate)#輸出結果
            plateList.append(Str)
            colorList.append(color_plate) 
            number_string = p.name.split(".")[0]
            numberList.append(int(number_string))
            list.clear()
    print(numberList)
    print(plateList)
    print(colorList)     






def color_Range(input):
    image = cv2.imread(str(input))

    # 定义颜色范围
    # 红色范围
    lower_red1 = np.array([0, 100, 100])     # 红色范围的下限1
    upper_red1 = np.array([10, 255, 255])    # 红色范围的上限1
    lower_red2 = np.array([160, 100, 100])   # 红色范围的下限2
    upper_red2 = np.array([179, 255, 255])   # 红色范围的上限2

    # 黄色范围
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([70, 255, 255])

    # 白色范围
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 38,255])

    # 将图像从BGR转换为HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 提取颜色区域
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask_white = cv2.inRange(hsv, lower_white, upper_white)

    # 计算特定颜色的像素数量
    red_pixels = cv2.countNonZero(mask_red)
    yellow_pixels = cv2.countNonZero(mask_yellow)
    white_pixels = cv2.countNonZero(mask_white)

    
    print("red_pixels:",red_pixels)
    print("yellow_pixels:",yellow_pixels)
    print("white_pixels:",white_pixels)

    # 判断哪种颜色占比最高
    color_counts = {'Red': red_pixels, 'Yellow': yellow_pixels, 'White': white_pixels}
    max_color = max(color_counts, key=color_counts.get)
    
    return max_color

 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default='weights/yolov7_plate_0421.pt', help='model.pt path(s)')
    parser.add_argument('--source', type=str, default='platePic', help='source')  # file/folder, 0 for webcam
    #parser.add_argument('--source', type=str, default='pic/tester/HSR-1785 02.jpg', help='source')  
    parser.add_argument('--img-size', type=int, default= 160, help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.7, help='object confidence threshold')
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

    


    with torch.no_grad():
        if opt.update:  # update all models (to fix SourceChangeWarning)
            for opt.weights in ['yolov7.pt']:
                detect()
                strip_optimizer(opt.weights)
        else:
            detect()
            