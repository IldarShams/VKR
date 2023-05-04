import sys

import anvil
import cv2
from anvil import server
from pygrabber.dshow_graph import FilterGraph
from PyQt6.QtCore import QThread, pyqtSignal
from multiprocessing import Queue
from TensorFlowYOLOv3.yolov3.utils import *
from TensorFlowYOLOv3.yolov3.configs import *

class VideoThread(QThread):
    video_frame_available = pyqtSignal(object)

    def __init__(self, to_emitter: Queue, from_emitter: Queue, device: str, from_gui: Queue):
        super().__init__()
        self.graph = FilterGraph()
        self.showBB = None
        self.to_emitter = to_emitter
        self.from_emitter = from_emitter
        self.command = from_gui
        self.device = self.graph.get_input_devices().index(device)
        self.cap = cv2.VideoCapture(self.device)
        if not self.cap.isOpened():
            print("Cannot open camera")
            exit(1)

    def run(self):
        while True:
            try:
                if not self.command.empty():
                    c = self.command.get()
                    if c == "exit":
                        self.cap.release()
                        return
                    elif c == "mode":
                        self.showBB = self.command.get()

                ret, frame = self.cap.read()
                if not ret:
                    exit(1)
                if self.showBB:
                    self.to_emitter.put("video")
                    self.to_emitter.put(frame)
                    bboxes = self.from_emitter.get()
                    frameYolo = draw_bbox(frame,
                                  bboxes,
                                  CLASSES=TRAIN_CLASSES,
                                  rectangle_colors=(255, 0, 0))

                else:
                    frameYolo = frame
                self.video_frame_available.emit(frameYolo)
            except Exception as e:
                print(e)
                return

