from PySide6.QtCore import QThread, Signal, QTimer, QTime
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPixmap
from numpy import ndarray

class VideoPreviewWidget(QWidget):
    def __init__(self, video_input, preview, video_time_text):
        super().__init__()
        video_clip = video_input
        self.preview = preview
        
        # Start the frame grabbing threa
        self.frame_grab = FrameGrab(video_clip, video_time_text)
        self.frame_grab.frameReady.connect(self.update_frame)
        self.frame_grab.start()

        self.slider_timer = QTimer(self)
        self.slider_timer.setSingleShot(True)
        self.slider_timer.timeout.connect(self.apply_update)

        self.update_type = None
        self.new_time_value = 0

    def set_time(self, value, update_type):
        self.new_time_value = value
        self.update_type = update_type
        self.slider_timer.start(300)

    def apply_update(self):
        if self.update_type == "start":
            self.frame_grab.update_start(self.new_time_value)
        elif self.update_type == "end":
            self.frame_grab.update_end(self.new_time_value)

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

    def __init__(self, video_clip, video_time_text):
        super().__init__()
        self.video_clip = video_clip
        self.running = True
        self.start_time = 0
        self.timer = 0
        self.video_time_text = video_time_text
        self.duration = self.video_clip.duration
        self.end_time = self.duration

    def update_start(self, time):
        self.stop()
        self.start_time = time
        self.timer = time
        self.play()

    def update_end(self, time):
        self.duration = time
        self.end_time = time

    def run(self):
        fps = self.video_clip.fps
        frame_interval = 1 / fps
        while self.timer < self.duration:
            if self.running:
                frame = self.video_clip.get_frame(self.timer)  # Get frame at current time
                self.frameReady.emit(frame)  # Send frame via signal
                self.msleep(int(frame_interval * 1000))  # Sleep until the next frame
                self.timer += frame_interval
                self.video_time_text.setTime(self.seconds_to_time(self.timer))
                if self.timer >= self.duration:
                    self.timer = self.start_time
            
    def play(self):
        self.running = True
        if self.timer >= self.duration:
            self.timer = self.start_time

    def pause(self):
        self.running = False
        if self.timer >= self.duration:
            self.timer = self.start_time

    def stop(self):
        self.running = False
        self.timer = self.start_time

    def seconds_to_time(self, time):
        # Calculate maximum time from video duration (in seconds)
        hours = time // 3600
        minutes = (time % 3600) // 60
        seconds = time % 60
        formatted_time = QTime(hours, minutes, seconds)
        return formatted_time