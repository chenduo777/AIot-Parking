import numpy as np
import cv2
import pickle
import argparse
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.widgets import PolygonSelector
from matplotlib.collections import PatchCollection
import sys  
import time
import os

import subprocess

points = []
prev_points = []
patches = []
total_points = []

class SelectFromCollection(object):
    def __init__(self, ax):
        self.canvas = ax.figure.canvas
        self.poly = PolygonSelector(ax, self.onselect)
        self.ind = []

    def onselect(self, verts):
        global points
        points = verts
        self.canvas.draw_idle()

    def disconnect(self):
        self.poly.disconnect_events()
        self.canvas.draw_idle()

def break_loop(event):
    global globSelect, savePath
    if event.key == 'b':
        globSelect.disconnect()
        print("Data saved in " + savePath + " file")
        with open(savePath, 'wb') as f:
            pickle.dump(total_points, f, protocol=pickle.HIGHEST_PROTOCOL)
        plt.close()
        sys.exit() 

def onkeypress(event):
    global points, prev_points, total_points
    if event.key == 'n':
        pts = np.array(points, dtype=np.int32)
        if points != prev_points and len(set(points)) == 4:
            print("Points: " + str(pts))
            patches.append(Polygon(pts))
            total_points.append(pts)
            prev_points = points
            points = []  # Reset points for the next region

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out_file', help="Name of the output file", default="regions.p")
    args = parser.parse_args()

    global globSelect
    global savePath
    savePath = args.out_file if args.out_file.endswith(".p") else args.out_file + ".p"
    
    print("from lift to right -------->\n")
    print("Press  'N'  to save the annotation\n")
    print("Press  'Q'  to continue annotating\n")
    print("Press  'B'  to finish annotation\n")
    print("Press 'Esc' to reset annotation \n")

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to capture frame")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        fig, ax = plt.subplots()
        ax.imshow(rgb_frame)

        p = PatchCollection(patches, alpha=0.7)
        p.set_array(10 * np.ones(len(patches)))
        ax.add_collection(p)

        globSelect = SelectFromCollection(ax)
        bbox = plt.connect('key_press_event', onkeypress)
        break_event = plt.connect('key_press_event', break_loop)

        plt.show()

    cap.release()