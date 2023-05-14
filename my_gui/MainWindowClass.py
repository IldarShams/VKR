import sys
import cv2
from datetime import datetime
import os
import json
from pygrabber.dshow_graph import FilterGraph
from multiprocessing import Queue, Lock, Pipe
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtCore import Qt
from my_gui.config import *
from my_gui.Emitter import *
from my_gui.VideoThread import *
from TensorFlowYOLOv3.yolov3.utils import *
from TensorFlowYOLOv3.yolov3.configs import *
import anvil.server

qt_creator_file = "./my_gui/test.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)



# anvil.server.connect("client_EC6WNV3EV2M5WPBYZKU6R4UU-VKPUFIU4RXBWF7MK")

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, to_emitter: Queue, from_emitter: Queue,
                 emitter: Emitter, lock: Lock):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.state = "image"

        self.emitter = emitter
        self.emitter.daemon = True
        self.emitter.start()
        self.to_emitter = to_emitter
        self.from_emitter = from_emitter
        self.lock = lock
        self.graph = FilterGraph()
        self.device = None
        self.vidth = None
        self.to_vidth = Queue()

        self.currentImage = None
        self.currentImageYolo = None

        self.dropNextImage = False
        self.image_scale = 1
        self.relVSlidePos = 0
        self.relHSlidePos = 0
        self.maxVSlidePos = 0
        self.maxHSlidePos = 0
        self.sizing = False

        try:
            self.videoDevices.addItems(["File System"] + self.graph.get_input_devices())
        except Exception as e:
            self.videoDevices.addItems(["File System"])

        self.nextButton.pressed.connect(lambda: self.nextImage(True))
        self.backButton.pressed.connect(lambda: self.nextImage(False))
        self.emitter.image_available.connect(self.getImageFromYolo)
        self.browserPathButton.pressed.connect(self.getImagesDirectory)
        self.videoDevices.currentIndexChanged.connect(self.videoDeviceChanged)
        self.browserPathLineEdit.textChanged.connect(self.imagesPathChanged)
        self.showBoxesRB.clicked.connect(self.showBB_changed)
        self.saveButton.clicked.connect(self.saveImage)
        self.savePathButton.clicked.connect(self.getSavePathDirectory)
        self.images = None
        self.browserPathLineEdit.setText("")
        self.emitter.status_message.connect(self.put_status)

        self.scrollArea.verticalScrollBar().rangeChanged.connect(self.scrollBarRangeChanged)
        self.scrollArea.horizontalScrollBar().rangeChanged.connect(self.scrollBarRangeChanged)
        self.scrollArea.verticalScrollBar().valueChanged.connect(self.scrollBarValueChanged)
        self.scrollArea.horizontalScrollBar().valueChanged.connect(self.scrollBarValueChanged)
        self.currentVSlidePos = 0
        self.currentHSlidePos = 0
        self.delta = 1

        # test section


        self.rb = QtWidgets.QRadioButton()
        self.l = QtWidgets.QLabel()
        # self.scroll = QtWidgets.QScrollArea()
        self.test = QtWidgets.QComboBox()
        self.but = QtWidgets.QPushButton()
        self.but.setEnabled(True)

        # print(self.imageLabel.size[0])
        # self.but.pressed.connect()
        self.rb.isChecked()
        # self.test.currentText()
        # self.rb.clicked()
        self.lineedit = QtWidgets.QLineEdit()

        self.scrollAreaContent.setMinimumSize(802, 479)
        self.imageLabel.setMinimumSize(802, 479)
        self.scrollAreaContent.resize(802, 479)
        self.imageLabel.resize(802, 479)
        try:
            with open("./config.json") as config:
                c = json.load(config)

                SAVE_DIR = c["SAVE_PATH"]
                IMAGE_DIR = c["IMAGE_DIR"]
                if os.path.isdir(SAVE_DIR):
                    self.savePathLineEdit.setText(SAVE_DIR)
                if os.path.isdir(IMAGE_DIR):
                    self.browserPathLineEdit.setText(IMAGE_DIR)
        except Exception as e:
          self.statusbar.showMessage("Main: ошибка файла конфигурации")

    # test section
    # server_UEMV3BW3LSDTQKDRMBFZRZKQ-VKPUFIU4RXBWF7MK
    # client_EC6WNV3EV2M5WPBYZKU6R4UU-VKPUFIU4RXBWF7MK
    # Секция ГУИ
    # def test(self):
    #     try:
    #         im = cv2.imread(self.images[self.currentImage])
    #         _, bts = cv2.imencode('.webp', im)
    #         # print(type(bts))
    #         # bts = bts.tostring()
    #         # print(bts)
    #         # print(type(bts))
    #         # ext = "." + (self.images[self.currentImage]).split(".")[1]
    #         # print(ext)
    #         # bytes = cv2.imencode(ext, im)
    #         anvil.server.call('process_image', bts)
    #     except Exception as e:
    #         print(e)

    def scrollBarRangeChanged(self, min=0, max=0):
        if self.sizing:
            self.currentVSlidePos = self.scrollArea.verticalScrollBar().sliderPosition() + 1
            self.currentHSlidePos = self.scrollArea.horizontalScrollBar().sliderPosition() + 1
            self.maxVSlidePos = self.scrollArea.verticalScrollBar().maximum()
            self.maxHSlidePos = self.scrollArea.horizontalScrollBar().maximum()
            if self.maxHSlidePos == 0:
                self.maxHSlidePos = 2
            if self.maxVSlidePos == 0:
                self.maxVSlidePos = 2
            self.relVSlidePos =  self.currentVSlidePos / self.maxVSlidePos
            self.relHSlidePos =  self.currentHSlidePos / self.maxHSlidePos

    def scrollBarValueChanged(self, val):
        if self.sizing:
            self.scrollArea.verticalScrollBar().setSliderPosition(int(self.currentVSlidePos* self.delta))
            self.scrollArea.horizontalScrollBar().setSliderPosition(int(self.currentHSlidePos * self.delta))
            # print(min, max)

    def updateImage(self):
        try:
            # self.scrollArea.updateGeometry()
            s = self.scrollArea.size()
            h = int(s.height() * self.image_scale)
            w = int(s.width() * self.image_scale)
            # print(w, h)
            self.imageLabel.resize(w, h)
            # print(self.state)
            if self.state == "image":
                self.putImageToLabel()

        except Exception as e:
            print(e)

    def keyPressEvent(self, event):
        try:
            if event.key() == 16777249:
                self.sizing = True

                self.currentVSlidePos = self.scrollArea.verticalScrollBar().sliderPosition()
                self.currentHSlidePos = self.scrollArea.horizontalScrollBar().sliderPosition()
                self.maxVSlidePos = self.scrollArea.verticalScrollBar().maximum()
                self.maxHSlidePos = self.scrollArea.horizontalScrollBar().maximum()
                if self.maxHSlidePos == 0:
                    self.maxHSlidePos = 2
                if self.maxVSlidePos == 0:
                    self.maxVSlidePos = 2
                self.relVSlidePos = self.currentVSlidePos / self.maxVSlidePos
                self.relHSlidePos = self.currentHSlidePos / self.maxHSlidePos

        except Exception as e:
            print(e)

    def keyReleaseEvent(self, event):
        try:

            if event.key() == 16777249:

                self.sizing = False

                # print(self.maxVSlidePos, self.maxHSlidePos)
        except Exception as e:
            print(e)

    def wheelEvent(self, event):
        try:
            if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
                self.delta = event.angleDelta().y() / 1200 / 2
                self.image_scale += self.delta
                self.delta += 1
                if (self.image_scale < 0):
                    self.image_scale = 0
                # maxVSlidePos = self.maxVSlidePos * self.image_scale
                # maxHSlidePos = self.maxHSlidePos * self.image_scale

                # self.scrollArea.verticalScrollBar().setSliderPosition(int(self.relVSlidePos * self.maxVSlidePos))
                # self.scrollArea.horizontalScrollBar().setSliderPosition(int(self.relHSlidePos * self.maxHSlidePos))
                s = self.scrollArea.size()
                h = int(s.height() * self.image_scale)
                w = int(s.width() * self.image_scale)
                self.scrollAreaContent.setMinimumSize(w, h)
                self.scrollAreaContent.resize(w, h)
                self.imageLabel.setMinimumSize(w, h)
                # self.maxVSlidePos = self.scrollArea.verticalScrollBar().maximum()
                # self.maxHSlidePos = self.scrollArea.horizontalScrollBar().maximum()
                # self.scrollArea.verticalScrollBar().setSliderPosition(int(self.relVSlidePos * self.maxVSlidePos))
                # self.scrollArea.horizontalScrollBar().setSliderPosition(int(self.relHSlidePos * self.maxHSlidePos))



                self.updateImage()

        except Exception as e:
            print(e)

    def resizeEvent(self, event):
        self.imageLabel.clear()
        self.updateImage()

    def put_status(self, text):
        self.statusbar.showMessage(text)

    # Изменение способа ввода изображения
    def videoDeviceChanged(self):
        try:
            if self.videoDevices.currentIndex() == 0:
                if self.vidth is not None:
                    try:
                        if self.vidth.isRunning():
                            self.to_vidth.put("exit")
                            if self.vidth.wait():
                                print("Main: Поток закрыт")
                    except Exception as e:
                        print(e)
                self.browserPathButton.setEnabled(True)
                self.browserPathLineEdit.setEnabled(True)
                self.nextButton.setEnabled(True)
                self.backButton.setEnabled(True)
                self.device = None
                self.state = "image"

            else:
                if self.vidth is not None:
                    try:
                        if self.vidth.isRunning():
                            self.to_vidth.put("exit")
                            if self.vidth.wait():
                                print("Main: Поток закрыт")
                    except Exception as e:
                        print(e)
                while not self.to_vidth.empty():
                    self.to_vidth.get()
                self.browserPathButton.setEnabled(False)
                self.browserPathLineEdit.setEnabled(False)
                self.nextButton.setEnabled(False)
                self.backButton.setEnabled(False)
                self.state = "video"
                self.device = self.videoDevices.currentText()
                self.videoProcessing()
        except Exception as e:
            print(e)

    # Переход к след изобр в папке, обработка в йоло
    def nextImage(self, direction: bool):
        try:
            if not self.showBoxesRB.isChecked():
                if not self.lock.acquire(block=False):
                    self.dropNextImage = True
                else:
                    self.lock.release()

            use_yolo = self.showBoxesRB.isChecked()
            if use_yolo:
                self.statusbar.showMessage("Main: взятие лока")
                if not self.lock.acquire(block=False):
                    self.statusbar.showMessage("Main: сеть занята, нет возможности перейти к след. изобр")
                    return
            if direction:
                self.currentImage += 1
            else:
                self.currentImage -= 1
            self.currentImage = self.currentImage % len(self.images)
            self.currentImageYolo = None
            if use_yolo:
                self.sendImageToYolo(self.images[self.currentImage])
            self.putImageToLabel()
        except AttributeError as e:
            print(str(e))
            print("Путь не задан")
            self.statusbar.showMessage("Путь не задан")
        except Exception as e:
            print(str(e))
            print("Что то не так!")

    # "C:\\Users\\User\\PycharmProjects\\CNN1\\TensorFlowYOLOv3\\IMAGES\\B0015_0001.png"

    # Изменение пути к папке с изобр
    def getImagesDirectory(self):
        self.browserPathLineEdit.setText(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Выберете папку с изображениями",
                                                       "./", QtWidgets.QFileDialog.Option.ShowDirsOnly))
    def getSavePathDirectory(self):
        self.savePathLineEdit.setText(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Выберете папку для сохранения",
                                                       "./", QtWidgets.QFileDialog.Option.ShowDirsOnly))
    # Обновление генератора
    def imagesPathChanged(self):
        self.getImagesFromDir(self.browserPathLineEdit.text())

    # Вывод изображения на окно: форматирование и выбор йоло или сурс
    def putImageToLabel(self, mode="image"):
        if mode == "image":
            if self.currentImage is None:
                return
            if self.currentImageYolo is None or not self.showBoxesRB.isChecked():
                image = self.resizeImage(cv2.imread(self.images[self.currentImage]))
            else:
                image = self.currentImageYolo
        else:  # video
            image = self.resizeImage(self.currentImageYolo)
        self.showImage(image)

    # Вывод изображения на окно: вывод в лайбл
    def showImage(self, image):
        qformat = QtGui.QImage.Format.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QtGui.QImage.Format.Format_RGBA8888
            else:
                qformat = QtGui.QImage.Format.Format_RGB888
            img = QtGui.QImage(image.data,
                               image.shape[1],
                               image.shape[0],
                               image.strides[0],  # <--- +++
                               qformat)
            img = img.rgbSwapped()
            self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(img))
            self.imageLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    # Закрытие окна
    def closeEvent(self, event):
        try:
            self.to_emitter.put("exit")
        except Exception as e:
            print(e)
        if self.vidth is not None:
            try:
                if self.vidth.isRunning():
                    self.to_vidth.put("exit")
                    if self.vidth.wait():
                        print("Main: Поток закрыт")
            except Exception as e:
                print(e)
        QtWidgets.QMainWindow.closeEvent(self, event)

    # Показать ограничивающие области радио батон чек
    def showBB_changed(self, show_bb: bool):
        if self.state == "video":
            self.to_vidth.put("mode")
            self.to_vidth.put(show_bb)
        else:  # image
            if show_bb and self.currentImage is not None:
                if self.currentImageYolo is None:
                    print("Main: взятие лока")
                    self.statusbar.showMessage("Main: взятие лока")
                    if not self.lock.acquire(block=False):
                        print("Main: yolo занята, нет возможности перейти к след. изобр")
                        self.statusbar.showMessage("Main: yolo занята, нет возможности перейти к след. изобр")
                        return
                    self.sendImageToYolo(self.images[self.currentImage])
                else:
                    self.putImageToLabel()
            else:
                self.putImageToLabel()

    # Секция ГУИ

    # Секция йоло

    def sendImageToYolo(self, im: str):
        self.to_emitter.put("image")
        print("Main: Отправка изображения к yolo")
        self.statusbar.showMessage("Main: Отправка изображения к yolo")
        self.to_emitter.put(im)

    def getImageFromYolo(self, bboxes):
        try:
            if self.dropNextImage:
                self.dropNextImage = False
                self.lock.release()
                self.currentImageYolo = None
                return
            self.statusbar.showMessage("Main: рисуем области")
            self.currentImageYolo = self.resizeImage(
                draw_bbox(cv2.imread(self.images[self.currentImage]),
                          bboxes,  # self.from_emitter.get(),
                          CLASSES=TRAIN_CLASSES,
                          rectangle_colors=(255, 0, 0))
            )
            self.statusbar.showMessage("Main: релиз лока")
            self.lock.release()
            self.putImageToLabel()
        except Exception as e:
            print(e)

    # Секция йоло

    # Секция утилиты
    # Запуск потока для обработки видео
    def videoProcessing(self):
        try:
            self.vidth = VideoThread(self.to_emitter, self.from_emitter,
                                     self.device, self.to_vidth)
            self.vidth.video_frame_available.connect(self.getImageFromVid)
            self.vidth.daemon = True
            self.to_vidth.put("mode")
            self.to_vidth.put(self.showBoxesRB.isChecked())
            self.vidth.start()

        except Exception as e:
            print(e)

    def getImageFromVid(self, im):
        self.currentImageYolo = im
        self.putImageToLabel(mode="video")

    # резайз изобр под корректный вывод в лайбл
    def resizeImage(self, image):
        try:
            w_w = self.imageLabel.size().width() - 5
            w_h = self.imageLabel.size().height() - 5
            # print(w_w, w_h)
            im_h = image.shape[0]
            im_w = image.shape[1]
            # print(im_w, im_h)
            if im_w > w_w:
                k = im_w / w_w
                im_w = w_w
                im_h = round(im_h / k)
            if im_h > w_h:
                k = im_h / w_h
                im_h = w_h
                im_w = round(im_w / k)
            if im_w < w_w and im_h < w_h:
                if w_w - im_w > w_h - im_h:
                    k = im_h / w_h
                    im_h = w_h
                    im_w = round(im_w / k)
                else:
                    k = im_w / w_w
                    im_w = w_w
                    im_h = round(im_h / k)
            # print(im_w, im_h)
            im = cv2.resize(image, (im_w, im_h))
            return im
        except Exception as e:
            print(e)
            return image

    # Генератор изобр для ввода из папки
    def getImagesFromDir(self, path):
        self.images = []
        if path == "":
            self.currentImage = None
            return
        try:
            for image in os.listdir(path):
                if image.__contains__(".png") or image.__contains__(".jpg"):
                    self.images.append(path + "/" + image)
            if len(self.images) > 0:
                self.currentImage = 0
                self.putImageToLabel()
            else:
                self.currentImage = None
            # print(self.images)
            # print(self.currentImage)
        except os.error:
            print("os.error")

    def saveImage(self):
        if self.showBoxesRB.isChecked() and not self.currentImageYolo is None:
            if not os.path.isdir(self.savePathLineEdit.text()):
                self.statusbar.showMessage("Main: каталог " + self.savePathLineEdit.text() + " не существует")
            else:
                now = datetime.now()
                path = os.path.join(self.savePathLineEdit.text(), now.strftime("%d_%m_%Y_%H_%M_%S") + ".jpg")

                print("Main: Сохранение " + path)
                self.statusbar.showMessage("Main: Сохранение " + path)
                try:
                    cv2.imwrite(os.path.join(SAVE_DIR, path), self.currentImageYolo)
                except Exception as e:
                    print(e)
                print("Main: Сохранён " + path)
                self.statusbar.showMessage("Main: Сохранён " + path)

# Секция утилиты
