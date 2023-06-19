from my_gui.MainWindowClass import *
from my_gui.MessageWindowClass import *
from YOLO_process import *
from my_gui.Emitter import *
from multiprocessing import Pipe
import sys

# import os
# os.system("cd")
mode = None

if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            mode = None
        elif len(sys.argv) == 2:
            if sys.argv[1] == "web":
                mode = "web"
            elif sys.argv[1] == "process":
                mode = "process"
            # elif sys.argv[1] == "local":
            #     mode = "local"
            else:
                sys.exit(1)
        else:
            sys.exit(1)

        if mode == "process":
            queue_form_emitter_to_yolo = Queue()
            queue_from_yolo_to_emitter = Queue()
        else:
            queue_form_emitter_to_yolo = None
            queue_from_yolo_to_emitter = None
        queue_form_win_to_emitter = Queue()
        queue_from_emitter_to_win = Queue()
        lock = Lock()

        app = QApplication(sys.argv)

        # запуск процесса нейронки
        emitter = Emitter(queue_form_emitter_to_yolo,
                          queue_from_yolo_to_emitter,
                          queue_form_win_to_emitter,
                          queue_from_emitter_to_win, mode)
        if mode == "process":
            yolo = YoloProcess(queue_form_emitter_to_yolo, queue_from_yolo_to_emitter, lock)
            yolo.start()
            pass

        window = MainWindow(queue_form_win_to_emitter, queue_from_emitter_to_win, emitter, lock)
        window.show()
        app.exec()
    except Exception as e:
        print(e)
        sys.exit(1)
