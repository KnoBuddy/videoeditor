import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QCheckBox, QLineEdit,
    QFileDialog, QMessageBox
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QThread, Signal

from moviepy.video.io.VideoFileClip import VideoFileClip

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
        
        # Load the UI file
        ui_file = QFile(ui_file_path)
        if not ui_file.open(QFile.ReadOnly):
            print(f"Cannot open {ui_file_path}: {ui_file.errorString()}")
            sys.exit(-1)
        
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        if not self.ui:
            print(loader.errorString())
            sys.exit(-1)
        
        # Access UI elements
        self.run_button = self.findChild(QPushButton, 'run')
        self.start_check = self.findChild(QCheckBox, 'start_time_check')
        self.end_check = self.findChild(QCheckBox, 'end_time_check')
        self.res_w_check = self.findChild(QCheckBox, 'res_w_check')
        self.res_h_check = self.findChild(QCheckBox, 'res_h_check')
        self.start_time = self.findChild(QLineEdit, 'start_text')
        self.end_time = self.findChild(QLineEdit, 'end_text')
        self.res_w = self.findChild(QLineEdit, 'res_w_text')
        self.res_h = self.findChild(QLineEdit, 'res_h_text')
        self.input_file_text = self.findChild(QLineEdit, 'input_file_text')
        self.output_file_text = self.findChild(QLineEdit, 'output_file_text')
        self.input_file_button = self.findChild(QPushButton, 'input_file_button')
        self.output_file_button = self.findChild(QPushButton, 'output_file_button')
        
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
        output_file = self.output_file_text.text()
        
        if not input_file or not output_file:
            QMessageBox.warning(self, "Error", "Please specify input and output files.")
            return
        
        # Initialize variables
        clip_begin = None
        clip_end = None
        resolution_w = None
        resolution_h = None
        
        # Get values from check boxes and text inputs
        if self.start_check.isChecked():
            try:
                clip_begin = float(self.start_time.text())
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid start time.")
                return
        if self.end_check.isChecked():
            try:
                clip_end = float(self.end_time.text())
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid end time.")
                return
        if self.res_w_check.isChecked():
            try:
                resolution_w = int(self.res_w.text())
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid resolution width.")
                return
        if self.res_h_check.isChecked():
            try:
                resolution_h = int(self.res_h.text())
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid resolution height.")
                return
        
        def process_video():
            try:
                # Open the video file
                video = VideoFileClip(input_file)
                
                # Apply subclip if needed
                if clip_begin is not None or clip_end is not None:
                    video = video.subclip(clip_begin, clip_end)
                
                # Apply resize if needed
                if resolution_w is not None and resolution_h is not None:
                    video = video.resize(newsize=(resolution_w, resolution_h))
                elif resolution_w is not None:
                    video = video.resize(width=resolution_w)
                elif resolution_h is not None:
                    video = video.resize(height=resolution_h)
                
                # Save the edited video
                video.write_videofile(output_file, codec="libx264", audio_codec="aac")
                
                self.update_status("Video processing completed successfully.")
            
            except Exception as e:
                self.update_status(f"An error occurred: {e}")
        
        # Start video processing in a separate thread
        self.thread = VideoProcessingThread(process_video)
        self.thread.finished.connect(self.thread.quit)
        self.thread.start()

    def update_status(self, message):
        QMessageBox.information(self, "Status", message)

if __name__ == "__main__":
    app = QApplication([])
    window = VideoEditor()
    window.show()
    sys.exit(app.exec())
