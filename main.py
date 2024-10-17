# To Do:
# Add Sliders for Beginning and End
# Add preview img/video

import sys
import os
import platform
import proglog

from moviepy.video.io.VideoFileClip import VideoFileClip
import moviepy.audio.fx.all as afx
import ffmpeg

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QCheckBox, QLineEdit, QFileDialog, QMessageBox, QSlider, QTimeEdit, QProgressBar, QLabel, QStyle
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QThread, Signal, QTime, QTimer
from PySide6.QtGui import QFontDatabase, QFont, QIntValidator, QIcon

import resources_rc
from preview import *

# Set the OpenGL attribute before creating the QApplication
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

cwd = os.getcwd()

class VideoProcessingThread(QThread):
    progress = Signal(int)
    finished = Signal()

    def __init__(self, input_file, output_file, clip_begin, clip_end, resolution_w, resolution_h, volume, new_bitrate):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.clip_begin = clip_begin
        self.clip_end = clip_end
        self.resolution_w = resolution_w
        self.resolution_h = resolution_h
        self.volume = volume
        self.new_bitrate = new_bitrate

    def run(self):
        class CustomLogger(proglog.ProgressBarLogger):
            def __init__(self, progress_signal):
                super().__init__()
                self.progress_signal = progress_signal

            def bars_callback(self, bar, attr, value, old_value=None):
                # This method is called whenever an attribute of a bar changes
                if bar == 't' and attr == 'index':
                    total = self.bars['t']['total']
                    index = value
                    progress = index / total
                    percentage = int(progress * 100)
                    self.progress_signal.emit(percentage)


        try:
            logger = CustomLogger(self.progress)

            # Proceed with video processing
            video = VideoFileClip(self.input_file)
            if self.clip_begin or self.clip_end:
                video = video.subclip(self.clip_begin, self.clip_end)
            if self.resolution_w and self.resolution_h:
                video = video.resize(newsize=(self.resolution_w, self.resolution_h))
            if self.volume is not None:
                video = video.fx(afx.volumex, self.volume)

            kwargs = {
                'codec': 'libx264',
                'audio_codec': 'aac',
                'logger': logger  # Use the custom logger
            }
            if self.new_bitrate:
                kwargs['bitrate'] = f'{self.new_bitrate}k'
            if not self.output_file:
                self.output_file = os.path.splitext(self.input_file)[0] + '-modified.mp4'
            else:
                self.output_file = self.output_file + '.mp4'

            # Write the video file with the custom logger
            video.write_videofile(self.output_file, **kwargs)
            print("Video created successfully")
        except Exception as e:
            print(f"Error processing video: {e}")
        finally:
            self.finished.emit()

    def update_progress(self, percentage):
        self.progress.emit(percentage)
    
    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)


class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        system = platform.system()

        # Path handling for the .ui file and fonts
        if hasattr(sys, '_MEIPASS'):
            # Packaged environment
            ui_file_path = os.path.join(sys._MEIPASS, 'gui.ui')
            font_path = os.path.join(sys._MEIPASS, 'fonts', 'digital-7 (mono).ttf')
            if system == 'Windows':
                icon_path = os.path.join(sys._MEIPASS, 'icons', 'videoeditor_icon.ico')
            else:
                icon_path = os.path.join(sys._MEIPASS, 'icons', 'videoeditor_icon.png')
        else:
            # Development environment
            ui_file_path = os.path.abspath('gui.ui')
            font_path = os.path.abspath('fonts/digital-7 (mono).ttf')
            if system == 'Windows':
                icon_path = os.path.abspath('icons/videoeditor_icon.ico')
            else:
                icon_path = os.path.abspath('icons/videoeditor_icon.png')

        loader = QUiLoader()
        
        self.ui = loader.load(ui_file_path)
        self.setCentralWidget(self.ui)
        self.setFixedSize(self.ui.size())
        self.setWindowTitle("Video Editor v0.1.0")
        self.setWindowIcon(QIcon(icon_path))

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
        self.progress_bar = self.ui.findChild(QProgressBar, 'progress_bar')
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)


        self.res_w.setValidator(QIntValidator(8, 7680, self))
        self.res_h.setValidator(QIntValidator(4, 4320, self))

        self.volume_slider = self.ui.findChild(QSlider, "volume_slider")
        self.volume_number = self.ui.findChild(QLineEdit, "volume_number")
        self.volume_number.setFont(QFont(font_family, 48))
        self.volume_number.setText(str(self.volume_slider.value()))
        self.volume_number.setValidator(QIntValidator(0, 200, self))

        self.start_time.setDisplayFormat("HH:mm:ss")
        self.end_time.setDisplayFormat("HH:mm:ss")

        self.start_time_slider = self.ui.findChild(QSlider, "start_time_slider")
        self.end_time_slider = self.ui.findChild(QSlider, "end_time_slider")
        self.start_time_slider.setRange(0, 0)
        self.end_time_slider.setRange(0, 0)

        self.preview = self.ui.findChild(QLabel, "preview")
        self.play = self.ui.findChild(QPushButton, "play")
        self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_pause = "play"

        self.stop = self.ui.findChild(QPushButton, "stop")
        self.stop.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.play_stop = "play"

        self.video_time_text = self.ui.findChild(QTimeEdit, "preview_time_text")

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
        self.play.clicked.connect(self.play_pause_clicked)
        self.stop.clicked.connect(self.stop_clicked)

    def play_pause_clicked(self):
        if self.input_file_text.text():
            if self.play_pause == "play":
                if self.play_stop == "stop":
                    self.preview_video.frame_grab.play()
                    self.play_stop = "play"
                    return
                self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
                self.preview_video.frame_grab.pause()
                self.play_pause = "pause"
            elif self.play_pause == "pause":
                self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
                self.preview_video.frame_grab.play()
                self.play_pause = "play"
    
    def stop_clicked(self):
        if self.input_file_text.text():
            self.preview_video.frame_grab.stop()
            self.play_stop = "stop"
    
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
        self.preview_video.set_time(value, "start", self.play_pause, self.play_stop)

    def slider_to_end_time(self, value):
        hours = value // 3600
        minutes = (value % 3600) // 60
        seconds = value % 60
        self.end_time.setTime(QTime(hours, minutes, seconds))
        self.start_time.setMaximumTime(QTime(hours, minutes, seconds))
        self.preview_video.set_time(value, "end")

    def start_time_to_slider(self):
        total_seconds = self.time_to_seconds(self.start_time.time())
        self.end_time_slider.setRange(total_seconds, self.video_duration)
        self.start_time_slider.blockSignals(True)
        self.start_time_slider.setValue(total_seconds)
        self.preview_video.set_time(total_seconds, "start", self.play_pause, self.play_stop)
        self.start_time_slider.blockSignals(False)

    def end_time_to_slider(self):
        total_seconds = self.time_to_seconds(self.end_time.time())
        self.start_time_slider.setRange(0, total_seconds)
        self.end_time_slider.blockSignals(True)
        self.end_time_slider.setValue(total_seconds)
        self.preview_video.set_time(total_seconds, "end")
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
        
        self.preview_video = VideoPreviewWidget(VideoFileClip(self.input_file_text.text(), target_resolution=(360, 640)), self.preview, self.video_time_text)

        # Calculate maximum time from video duration (in seconds)
        self.max_time = self.seconds_to_time(self.video_duration)

        self.start_time.setMaximumTime(self.max_time)
        self.end_time.setMaximumTime(self.max_time)
        self.start_time_slider.setRange(0, self.video_duration)
        self.end_time_slider.setRange(0, self.video_duration)
        self.slider_to_end_time(self.video_duration)
        self.end_time_to_slider()

    def run_button_clicked(self):
        print("Run button clicked")
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

        volume = float(self.volume_slider.value()/100)

        self.thread = VideoProcessingThread(
            input_file=self.input_file,
            output_file=self.output_file,
            clip_begin=clip_begin,
            clip_end=clip_end,
            resolution_w=resolution_w,
            resolution_h=resolution_h,
            volume=volume,
            new_bitrate=new_bitrate
        )

        # Connect the progress signal to the update method
        self.thread.progress.connect(self.update_progress_bar)
        print('Thread created and progress signal connected')
        self.thread.finished.connect(self.thread.quit)
        self.thread.start()

    def update_progress_bar(self, value):
        print(f"Updating progress bar to {value}%")
        self.progress_bar.setValue(value)

if __name__ == "__main__":
    # main()
    app = QApplication([])
    window = VideoEditor()
    window.show()
    sys.exit(app.exec())
