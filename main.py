# To Do:
# Add Sliders for Beginning and End
# Add preview img/video

import sys
import os
import argparse

from moviepy.video.io.VideoFileClip import VideoFileClip
import moviepy.audio.fx.all as afx
import ffmpeg

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QCheckBox, QLineEdit, QFileDialog, QMessageBox, QSlider, QTimeEdit
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QThread, Signal, QTime
from PySide6.QtGui import QFontDatabase, QFont, QIntValidator

import resources_rc

# Set the OpenGL attribute before creating the QApplication
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

cwd = os.getcwd()

updating = False

class VideoProcessingThread(QThread):
    progress = Signal(str)
    finished = Signal()

    def __init__(self, video_processing_function):
        super().__init__()
        self.video_processing_function = video_processing_function

    def run(self):
        self.video_processing_function()
        self.finished.emit()

class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        # Path handling for the .ui file and fonts
        if hasattr(sys, '_MEIPASS'):
            # Packaged environment
            ui_file_path = os.path.join(sys._MEIPASS, 'new_gui.ui')
            font_path = os.path.join(sys._MEIPASS, 'fonts', 'digital-7 (mono).ttf')
        else:
            # Development environment
            ui_file_path = os.path.abspath('new_gui.ui')
            font_path = os.path.abspath('fonts/digital-7 (mono).ttf')

        loader = QUiLoader()
        
        self.ui = loader.load(ui_file_path)
        self.setCentralWidget(self.ui)
        self.setFixedSize(self.ui.size())
        self.setWindowTitle("Video Editor v0.0.1")

        # Attempt to load the font
        font_id = QFontDatabase.addApplicationFont(font_path)

        if font_id < 0:
            print(f"Failed to load font from {font_path}")
        else:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font_family = font_families[0]
            else:
                print("Failed to retrieve font family")

        # Load objects
        self.run_button = self.ui.findChild(QPushButton, 'run')
        self.res_w_check = self.ui.findChild(QCheckBox, 'res_w_check')
        self.res_h_check = self.ui.findChild(QCheckBox, 'res_h_check')
        self.bitrate_check = self.ui.findChild(QCheckBox, "bitrate_check")
        self.start_time = self.ui.findChild(QTimeEdit, 'start_time_text')
        self.end_time = self.ui.findChild(QTimeEdit, 'end_time_text')
        self.res_w = self.ui.findChild(QLineEdit, 'res_w_text')
        self.res_h = self.ui.findChild(QLineEdit, 'res_h_text')
        self.bitrate_text = self.ui.findChild(QLineEdit, "bitrate_text")
        self.input_file_text = self.ui.findChild(QLineEdit, "input_file_text")
        self.input_file_button = self.ui.findChild(QPushButton,'input_file_button')
        self.output_file_check = self.ui.findChild(QCheckBox, "output_file_check")
        self.output_file_text = self.ui.findChild(QLineEdit, "output_file_text")

        self.res_w.setValidator(QIntValidator(8, 7680, self))
        self.res_h.setValidator(QIntValidator(4, 4320, self))

        self.volume_slider = self.ui.findChild(QSlider, "volume_slider")
        self.volume_number = self.ui.findChild(QLineEdit, "volume_number")
        self.volume_number.setFont(QFont(font_family, 48))
        self.volume_number.setText(str(self.volume_slider.value()))
        self.volume_number.setValidator(QIntValidator(0, 200, self))

        self.start_time_slider = self.ui.findChild(QSlider, "start_time_slider")
        self.end_time_slider = self.ui.findChild(QSlider, "end_time_slider")
        self.start_time_slider.setRange(0, 0)
        self.end_time_slider.setRange(0, 0)

        self.updating = False

        self.connect_objects()

    def connect_objects(self):
        self.run_button.clicked.connect(self.run_button_clicked)
        self.input_file_button.clicked.connect(self.select_input_file)
        self.volume_slider.valueChanged.connect(self.update_volume_lcd)
        self.volume_number.textChanged.connect(self.update_volume_slider)
        self.start_time_slider.valueChanged.connect(self.slider_to_start_time)
        self.start_time.timeChanged.connect(self.start_time_to_slider)
        self.end_time_slider.valueChanged.connect(self.slider_to_end_time)
        self.end_time.timeChanged.connect(self.end_time_to_slider)
    
    def update_volume_lcd(self, value):
        self.volume_number.setText(str(value))

    def update_volume_slider(self):
        # Block signals from the volume slider to prevent feedback loops
        self.volume_slider.blockSignals(True)
        
        text = self.volume_number.text()
        if text.isdigit():
            value = int(text)
            if self.volume_slider.minimum() <= value <= self.volume_slider.maximum():
                self.volume_slider.setValue(value)
            else:
                # If value is out of bounds, adjust it
                value = max(self.volume_slider.minimum(), min(value, self.volume_slider.maximum()))
                self.volume_slider.setValue(value)
                self.volume_number.setText(str(value))

        # Re-enable signals after the update
        self.volume_slider.blockSignals(False)

    def slider_to_start_time(self, value):
        hours = value // 3600
        minutes = (value % 3600) // 60
        seconds = value % 60
        self.start_time.setTime(QTime(hours, minutes, seconds))
        self.end_time.setMinimumTime(QTime(hours, minutes, seconds))

    def slider_to_end_time(self, value):
        hours = value // 3600
        minutes = (value % 3600) // 60
        seconds = value % 60
        self.end_time.setTime(QTime(hours, minutes, seconds))
        self.start_time.setMaximumTime(QTime(hours, minutes, seconds))

    def start_time_to_slider(self):
        total_seconds = self.time_to_seconds(self.start_time.time())
        self.end_time_slider.setRange(total_seconds, self.video_duration)
        self.start_time_slider.blockSignals(True)
        self.start_time_slider.setValue(total_seconds)
        self.start_time_slider.blockSignals(False)

    def end_time_to_slider(self):
        total_seconds = self.time_to_seconds(self.end_time.time())
        self.start_time_slider.setRange(0, total_seconds)
        self.end_time_slider.blockSignals(True)
        self.end_time_slider.setValue(total_seconds)
        self.end_time_slider.blockSignals(False)

    def time_to_seconds(self, time):
        total_seconds = time.hour() * 3600 + time.minute() * 60 + time.second()
        return total_seconds

    def seconds_to_time(self, time):
        # Calculate maximum time from video duration (in seconds)
        hours = time // 3600
        minutes = (time % 3600) // 60
        seconds = time % 60
        formatted_time = QTime(hours, minutes, seconds)
        return formatted_time

    def select_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input Video",
            os.path.expanduser(cwd),
            "Video Files (*.mp4 *.avi *.mov);;All Files (*)"
        )
        if file_name:
            if os.path.isfile(file_name):
                self.input_file_text.setText(file_name)
            else:
                QMessageBox.warning(self, "Invalid File", "The selected file is not valid.")

        self.video_duration = VideoFileClip(self.input_file_text.text()).duration

        # Calculate maximum time from video duration (in seconds)
        self.max_time = self.seconds_to_time(self.video_duration)

        self.start_time.setMaximumTime(self.max_time)
        self.end_time.setMaximumTime(self.max_time)
        self.start_time_slider.setRange(0, self.video_duration)
        self.end_time_slider.setRange(0, self.video_duration)
        self.slider_to_end_time(self.video_duration)
        self.end_time_to_slider()

    def run_button_clicked(self):
        self.input_file = self.input_file_text.text()

        if not self.input_file:
            print("No input file selected. Please input a filename to be edited.")
            return
        
        clip_begin = self.start_time_slider.value()
        clip_end = self.end_time_slider.value()
        resolution_w = None
        resolution_h = None

        if self.output_file_check.isChecked():
            try:
                self.output_file = str(self.output_file_text.text()).removesuffix('.mp4')
            except ValueError:
                self.output_file = None
                print("Invalid output name input.")
        else:
            self.output_file = None

        if self.res_w_check.isChecked():
            try:
                resolution_w = int(self.res_w.text())
            except ValueError:
                print("Invalid resolution width.")
                return
        if self.res_h_check.isChecked():
            try:
                resolution_h = int(self.res_h.text())
            except ValueError:
                print("Invalid resolution height.")
                return
        if self.bitrate_check.isChecked():
            try:
                new_bitrate = int(self.bitrate_text.text())
            except ValueError:
                print("Invalid bitrate.")
                new_bitrate = None
        else:
            new_bitrate = None


        def process_video():
            print(f"Clip Begin: {clip_begin}\n Clip End: {clip_end}")
            if clip_begin and clip_end:
                video = VideoFileClip(self.input_file, target_resolution=(resolution_w, resolution_h)).subclip(clip_begin, clip_end)
            elif clip_begin and not clip_end:
                video = VideoFileClip(self.input_file, target_resolution=(resolution_w, resolution_h)).subclip(clip_begin)
            elif clip_end and not clip_begin:
                video = VideoFileClip(self.input_file, target_resolution=(resolution_w, resolution_h)).subclip(0, clip_end)
            else:
                video = VideoFileClip(self.input_file, target_resolution=(resolution_w, resolution_h))
            # Adjust volume
            volume = float(self.volume_slider.value()/100)
            video = video.fx(afx.volumex, volume)

            kwargs = {
                'codec': 'libx264',
                'audio_codec': 'aac'
            }

            if not new_bitrate:
                print("No bitrate supplied. Supply bitrate or uncheck field.")

            if new_bitrate is not None and new_bitrate != '':
                kwargs['bitrate'] = f'{new_bitrate}k'

            if self.output_file == None or self.output_file == '':
                self.output_file = self.input_file.removesuffix(".mp4")
                output_mod = '-modified'
            else:
                output_mod = ''
            video.write_videofile(f"{self.output_file}{output_mod}.mp4", **kwargs)
        
        self.thread = VideoProcessingThread(process_video)
        self.thread.finished.connect(self.thread.quit)
        self.thread.start()


if __name__ == "__main__":
    # main()
    app = QApplication([])
    window = VideoEditor()
    window.show()
    sys.exit(app.exec())
