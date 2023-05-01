from my_gui.MainWindowClass import *
from my_gui.MessageWindowClass import *
from YOLO_process import *
from my_gui.Emitter import *
from multiprocessing import Pipe


# import sys
# import os
# os.system("cd")





if __name__ == "__main__":
    try:
        queue_form_win_to_emitter = Queue()
        queue_from_emitter_to_win = Queue()
        queue_form_emitter_to_yolo = Queue()
        queue_from_yolo_to_emitter = Queue()
        lock = Lock()

        app = QApplication(sys.argv)


        # запуск процесса нейронки
        emitter = Emitter(queue_form_emitter_to_yolo,
                          queue_from_yolo_to_emitter,
                          queue_form_win_to_emitter,
                          queue_from_emitter_to_win)
        # yolo = YoloProcess(queue_form_emitter_to_yolo, queue_from_yolo_to_emitter, lock)
        # yolo.start()

        window = MainWindow(queue_form_win_to_emitter, queue_from_emitter_to_win, emitter, lock)
        window.show()
        app.exec()
    except Exception as e:
        print(e)
        exit(1)