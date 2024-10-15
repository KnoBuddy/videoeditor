from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPixmap
from numpy import ndarray

class VideoPreviewWidget(QWidget):
    def __init__(self, video_input, preview):
        super().__init__()
        video_clip = video_input
        self.preview = preview
        
        # Start the frame grabbing thread
        self.frame_grab = FrameGrab(video_clip)
        self.frame_grab.frameReady.connect(self.update_frame)
        self.frame_grab.start()

    def update_frame(self, frame):
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        self.preview_label = self.preview.setPixmap(pixmap)

    def closeEvent(self, event):
        self.frame_fetcher.stop()  # Stop the thread when the widget is closed
        self.frame_fetcher.wait()
        super().closeEvent(event)


class FrameGrab(QThread):
    frameReady = Signal(ndarray)

    def __init__(self, video_clip):
        super().__init__()
        self.video_clip = video_clip
        self.running = True
        self.timer = 0
        self.duration = self.video_clip.duration

    def update_start(self, time):
        self.stop()
        self.timer = time

    def update_end(self, time):
        self.duration = time

    def run(self):
        fps = self.video_clip.fps
        frame_interval = 1 / fps
        while self.timer < self.duration:
            if self.running:
                frame = self.video_clip.get_frame(self.timer)  # Get frame at current time
                self.frameReady.emit(frame)  # Send frame via signal
                self.msleep(int(frame_interval * 1000))  # Sleep until the next frame
                self.timer += frame_interval
            else:
                pass
    def play(self):
        self.running = True

    def pause(self):
        self.running = False

    def stop(self):
        self.running = False
        self.timer = 0