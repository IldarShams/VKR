import sys

import anvil
import cv2
from anvil import server
from PyQt6.QtCore import QThread, pyqtSignal
from multiprocessing import Queue


class Emitter(QThread):
    image_available = pyqtSignal(object)
    status_message = pyqtSignal(str)

    def __init__(self, send_yolo: Queue, get_yolo: Queue, get_gui: Queue, send_gui: Queue, mode: str):
        super().__init__()
        self.send_yolo = send_yolo
        self.get_yolo = get_yolo
        self.get_gui = get_gui
        self.send_gui = send_gui
        self.mode = mode
        if mode == "web":
            server.connect("client_EC6WNV3EV2M5WPBYZKU6R4UU-VKPUFIU4RXBWF7MK")

    def run(self):
        print("mode =", self.mode, self.mode == "process")
        if self.mode == "process":
            print("check")
            self.status_message.emit("YOLO: Загрузка...")
            command = self.get_yolo.get()
            print("check2")
            if command != "OK":
                self.status_message.emit("YOLO: Ошибка!")
                exit(1)
        while True:
            try:
                self.status_message.emit("YOLO: Сеть ожидает ввод")
                command = self.get_gui.get()
                if command == "exit":
                    self.send_yolo.put(command)
                    exit(0)
                # local
                if self.mode == "process":
                    image = self.get_gui.get()
                    self.send_yolo.put(command)
                    self.send_yolo.put(image)
                    bboxes = self.get_yolo.get()
                    # print(type(bboxes))
                    # print(bboxes)
                    self.status_message.emit("YOLO: Изображение обработано")
                    if command == "video":
                        self.send_gui.put(bboxes)
                    else:
                        self.image_available.emit(bboxes)

                if self.mode == "web":
                    image = self.get_gui.get()

                    if command == "image":
                        image = cv2.imread(image)

                    _, bts = cv2.imencode('.webp', image)
                    bts = bts.tostring()
                    itype = image.dtype
                    blobMedia = anvil.BlobMedia(content_type="image", content=bts, name="image")
                    print("Emitter: Передача изображения")
                    self.status_message.emit("Emitter: Передача изображения")
                    bboxes = server.call("process_image", blobMedia, "uint8")
                    self.status_message.emit("YOLO: Изображение обработано")
                    if command == "video":
                        self.send_gui.put(bboxes)
                    else:
                        self.image_available.emit(bboxes)
            except EOFError as e:
                # print("Emitter: Что то пошло не так")
                self.status_message.emit("Emitter: Что то пошло не так")
                print(e)
            except Exception as e:
                # print("Emitter: Что то пошло не так")
                self.status_message.emit("Emitter: Что то пошло не так")
                print(e)
            else:
                print("Emitter: Отправка сигнала окну")
                self.status_message.emit("Emitter: Отправка сигнала окну")
