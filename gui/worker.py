import queue
import threading
import asyncio
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from scanner.discovery import stream_scan

class ScanWorker(QObject):
    progress_signal = pyqtSignal()
    found_signal = pyqtSignal(dict)
    done_signal = pyqtSignal()

    def __init__(self, ip_list, speed, ports, local_ip):
        super().__init__()
        self.ip_list = ip_list
        self.speed = speed
        self.ports = ports
        self.local_ip = local_ip
        self.result_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_queue)

    def start(self):
        self.timer.start(50)
        self.thread = threading.Thread(target=self.run_async, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.timer.stop()

    def run_async(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                stream_scan(self.ip_list, self.speed, self.ports, self.local_ip, self.result_queue, self.stop_event)
            )
        finally:
            loop.close()

    def poll_queue(self):
        while not self.result_queue.empty():
            try:
                item = self.result_queue.get_nowait()
                if item["type"] == "progress":
                    self.progress_signal.emit()
                elif item["type"] == "found":
                    self.found_signal.emit(item["device"])
                elif item["type"] == "done":
                    self.done_signal.emit()
                    self.timer.stop()
            except queue.Empty:
                break
