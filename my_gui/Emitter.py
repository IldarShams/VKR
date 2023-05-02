import anvil
import cv2
from anvil import server
from PyQt6.QtCore import QThread, pyqtSignal
from multiprocessing import Queue


server.connect("client_EC6WNV3EV2M5WPBYZKU6R4UU-VKPUFIU4RXBWF7MK")
class Emitter(QThread):

    image_available = pyqtSignal(object)

    def __init__(self, send_yolo : Queue, get_yolo : Queue, get_gui : Queue, send_gui : Queue):
        super().__init__()
        # self.send_yolo = send_yolo
        # self.get_yolo = get_yolo
        self.get_gui = get_gui
        self.send_gui = send_gui

    def run(self):
        while True:
            try:
                # local

                # command = self.get_gui.get()
                # if command == "exit":
                #     self.send_yolo.put(command)
                # else:
                #     image = self.get_gui.get()
                #     self.send_yolo.put(command)
                #     self.send_yolo.put(image)
                #     bboxes = self.get_yolo.get()
                # print(type(bboxes))
                # print(bboxes)

                # print("Emitter: получили боксы")
                # print("Emitter: отправка боксов")
                # self.image_available.emit(bboxes)
                # signal = self.yolo_data.recv()
                # print("Emitter: Получен сигнал от йоло:", signal)


                #web
                command = self.get_gui.get()
                image = self.get_gui.get()

                if command == "image":
                    image = cv2.imread(image)

                _, bts = cv2.imencode('.webp', image)
                bts = bts.tostring()
                itype = image.dtype
                blobMedia = anvil.BlobMedia(content_type="image", content=bts, name="image")
                print("Emitter: Передача изображения")
                # for chunk in chunks:
                #     resp = server.call("get_chunk", str(chunk))
                # print("Emitter: Передача изображения окончена")
                bboxes = server.call("process_image", blobMedia, "uint8")
                print("Emitter: получили боксы")
                print("Emitter: отправка боксов")
                if command == "video":
                    self.send_gui.put(bboxes)
                else:
                    self.image_available.emit(bboxes)
            except EOFError:
                print("Emitter: Что то пошло не так")
            except Exception as e:
                # print("Emitter: Что то пошло не так")
                print(e)
            else:
                print("Emitter: Отправка сигнала окну")



