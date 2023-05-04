from multiprocessing import Process, Queue, Lock
from PyQt5.QtCore import pyqtSignal, QThread
from my_gui.Emitter import *
import os

os.environ['CUDA_VISIBLE_DEVICES'] = '0'
import cv2
import numpy as np
import tensorflow as tf
from pygrabber.dshow_graph import FilterGraph
from TensorFlowYOLOv3.yolov3.utils import *  #utils # import  detect_image, detect_image_for_vid, detect_realtime, detect_video, Load_Yolo_model, detect_video_realtime_mp
from TensorFlowYOLOv3.yolov3.configs import *


class YoloProcess(Process):
    def __init__(self, from_emitter: Queue, to_emitter: Queue, status_lock : Lock):
        super().__init__()
        self.commands = from_emitter
        self.send_im = to_emitter
        self.status_lock = status_lock


    def run(self):
        try:
            yolo = Load_Yolo_model()
            self.send_im.put("OK")
        except Exception as e:
            print(e)
            exit(1)
        command = ""
        while True:
            print("YOLO: Нейронка ожидает ввод")
            command = self.commands.get()
            if command == "exit":
                print("YOLO: выход")
                self.send_im.put("exit")
                break
            if command == "image":
                im = self.commands.get()
                print("YOLO: Изображение получено")
                # print(im)
                # cv2.imshow("im", im)
                bboxes = detect_image(yolo, im, "./IMAGES/plate_1_detect.jpg", input_size=YOLO_INPUT_SIZE,
                                     show=True, CLASSES=TRAIN_CLASSES, rectangle_colors=(255, 0, 0))
                print("YOLO: Изображение обработано")
                self.send_im.put(bboxes)
                # self.pipe_to_emitter.send("OK")
            if command == "video":
                im = self.commands.get()
                bboxes = detect_image_for_vid(yolo, im, "./IMAGES/plate_1_detect.jpg", input_size=YOLO_INPUT_SIZE,
                                     show=True, CLASSES=TRAIN_CLASSES, rectangle_colors=(255, 0, 0))
                self.send_im.put(bboxes)
            # exit(0)
