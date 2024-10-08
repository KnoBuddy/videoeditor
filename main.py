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
        
        self.ui = loader.load(ui_file_path, self)

        # Load objects
        self.run_button = self.findChild(QPushButton, 'run')
        self.start_check = self.findChild(QCheckBox, 'run')
        self.end_check = self.findChild(QCheckBox, 'run')
        self.res_w_check = self.findChild(QCheckBox, 'run')
        self.res_h_check = self.findChild(QCheckBox, 'run')
        self.start_time = self.findChild(QLineEdit, 'run')
        self.end_time = self.findChild(QLineEdit, 'run')
        self.res_w = self.findChild(QLineEdit, 'run')
        self.res_h = self.findChild(QLineEdit, 'run')
        self.input_file_text = self.findChild(QLineEdit, "input_file_text")
        self.input_file_button = self.findChild(QPushButton,'input_file_button')

        self.connect_objects()

    def connect_objects(self):
        if self.run_button:
            self.run_button.clicked.connect(self.run_button_clicked)
        else:
            print("Run button not found!")
        if self.input_file_button:
            self.input_file_button.clicked.connect(self.select_input_file)

    def select_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input Video")
        if file_name:
            self.input_file_text.setText(file_name)

    def run_button_clicked(self):

        input_file = self.input_file_text.text()

        if not self.input_file or not self.output_file:
            print("No input/output file selected. Please input a filename to be edited.")
            return
        
        clip_begin = None
        clip_end = None
        resolution_w = None
        resolution_h = None

        if self.start_check.isChecked():
            try:
                clip_begin = float(self.start_time.text())
            except ValueError:
                print("Invalid start time. Please enter the value in 00:00:00")
        if self.end_check.isChecked():
            try:
                clip_end = float(self.end_time.text())
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


        def process_video():
            try:
                video = VideoFileClip(input_file, target_resolution=(resolution_w, resolution_h)).subclip(clip_begin, clip_end)
                #if args.volume is not None:
                #    volume = float(args.volume)
                #    video = video.fx(afx.volumex, volume)
                video.write_videofile(f"Modified-{self.input_file}", codec="libx264", audio_codec="aac") # bitrate=args.bitrate)
            except Exception as e:
                print("An error occured in video processing: {e}")
        
        self.thread = VideoProcessingThread(process_video)
        self.thread.finished.connect(self.thread.quit)
        self.thread.start()


def arg_parser():
    parser = argparse.ArgumentParser(
        prog="Python Video Editor",
        description="Simple Video Clip/Quality/Resolution Editor"
    )

    parser.add_argument("-i", "--input")
    parser.add_argument('-o', "--output")
    parser.add_argument("-cb", "--clipbegin")
    parser.add_argument("-ce", "--clipend")
    parser.add_argument("-rw", "--resolutionw")
    parser.add_argument("-rh", "--resolutionh")
    parser.add_argument("-b", "--bitrate")
    parser.add_argument("-v", "--volume")

    args = parser.parse_args()

    return args

if __name__ == "__main__":
    # main()
    app = QApplication([])
    window = VideoEditor()
    window.ui.show()
    sys.exit(app.exec())
