import sys
import os
import argparse

from moviepy.video.io.VideoFileClip import VideoFileClip
import moviepy.audio.fx.all as afx
import ffmpeg

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QCheckBox, QLineEdit, QFileDialog, QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QThread, Signal

# Set the OpenGL attribute before creating the QApplication
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

cwd = os.getcwd()

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
        loader = QUiLoader()
        
        # Use absolute path for the .ui file for better debugging
        ui_file_path = os.path.abspath("gui.ui")
        print(f"Loading UI from: {ui_file_path}")
        
        self.ui = loader.load(ui_file_path)
        self.setCentralWidget(self.ui)
        self.setFixedSize(self.ui.size())


        # Load objects
        self.run_button = self.ui.findChild(QPushButton, 'run')
        self.start_check = self.ui.findChild(QCheckBox, 'start_time_check')
        self.end_check = self.ui.findChild(QCheckBox, 'end_time_check')
        self.res_w_check = self.ui.findChild(QCheckBox, 'res_w_check')
        self.res_h_check = self.ui.findChild(QCheckBox, 'res_h_check')
        self.start_time = self.ui.findChild(QLineEdit, 'start_text')
        self.end_time = self.ui.findChild(QLineEdit, 'end_text')
        self.res_w = self.ui.findChild(QLineEdit, 'res_w_text')
        self.res_h = self.ui.findChild(QLineEdit, 'res_h_text')
        self.bitrate_check = self.ui.findChild(QCheckBox, "bitrate_check")
        self.bitrate_text = self.ui.findChild(QLineEdit, "bitrate_text")
        self.input_file_text = self.ui.findChild(QLineEdit, "input_file_text")
        self.input_file_button = self.ui.findChild(QPushButton,'input_file_button')

        self.connect_objects()

    def connect_objects(self):
        if self.run_button:
            self.run_button.clicked.connect(self.run_button_clicked)
        else:
            print("Run button not found!")
        if self.input_file_button:
            self.input_file_button.clicked.connect(self.select_input_file)

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


    def run_button_clicked(self):

        if not self.input_file_text:
            print("No input file selected. Please input a filename to be edited.")
            return

        input_file = self.input_file_text.text()
        
        clip_begin = None
        clip_end = None
        resolution_w = None
        resolution_h = None

        if self.start_check.isChecked():
            try:
                clip_begin = self.start_time.text()
            except ValueError:
                print("Invalid start time. Please enter the value in 00:00:00")
        if self.end_check.isChecked():
            try:
                clip_end = self.end_time.text()
            except ValueError:
                print("Invalid start time. Please enter the value in 00:00:00")
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


        def process_video():
            if clip_begin and clip_end:
                video = VideoFileClip(input_file, target_resolution=(resolution_w, resolution_h)).subclip(clip_begin, clip_end)
            else:
                video = VideoFileClip(input_file, target_resolution=(resolution_w, resolution_h))
            #if args.volume is not None:
            #    volume = float(args.volume)
            #    video = video.fx(afx.volumex, volume)
            output_file = input_file.removesuffix(".mp4")
            if not new_bitrate:
                video.write_videofile(f"{output_file}-modified.mp4", codec="libx264", audio_codec="aac")
            else:
                video.write_videofile(f"{output_file}-modified.mp4", codec="libx264", audio_codec="aac", bitrate=f"{new_bitrate}k")
        
        self.thread = VideoProcessingThread(process_video)
        self.thread.finished.connect(self.thread.quit)
        self.thread.start()


if __name__ == "__main__":
    # main()
    app = QApplication([])
    window = VideoEditor()
    window.show()
    sys.exit(app.exec())
