import sys
import os
import concurrent.futures
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar, QTextEdit, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class JPEGRepairApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JPEG Extractor Tool")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()

        self.raw_label = QLabel("RAW Folder:")
        self.raw_path_edit = QLineEdit()
        self.raw_browse_button = QPushButton("Browse", self)
        self.raw_browse_button.setObjectName("browseButton")
        self.raw_browse_button.clicked.connect(self.browse_raw_folder)

        self.repaired_label = QLabel("Extracted Folder:")
        self.repaired_path_edit = QLineEdit()
        self.repaired_browse_button = QPushButton("Browse", self)
        self.repaired_browse_button.setObjectName("browseButton")
        self.repaired_browse_button.clicked.connect(self.browse_repaired_folder)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.extract_button = QPushButton("Extract", self)
        self.extract_button.setObjectName("blueButton")
        self.extract_button.clicked.connect(self.extract_jpeg_files)

        layout.addWidget(self.raw_label)
        layout.addWidget(self.raw_path_edit)
        layout.addWidget(self.raw_browse_button)
        layout.addWidget(self.repaired_label)
        layout.addWidget(self.repaired_path_edit)
        layout.addWidget(self.repaired_browse_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_box)
        layout.addWidget(self.extract_button)

        self.setLayout(layout)

        self.setStyleSheet("""
        #browseButton, #blueButton {
            background-color: #3498db;
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 4px;
        }
        #browseButton:hover, #blueButton:hover {
            background-color: #2980b9;
        }
        """)

    def browse_raw_folder(self):
        raw_folder = QFileDialog.getExistingDirectory(self, "Select RAW Folder")
        if raw_folder:
            self.raw_path_edit.setText(raw_folder)

    def browse_repaired_folder(self):
        repaired_folder = QFileDialog.getExistingDirectory(self, "Select Extracted Folder")
        if repaired_folder:
            self.repaired_path_edit.setText(repaired_folder)

    def extract_jpeg_files(self):
        raw_folder_path = self.raw_path_edit.text()
        repaired_folder_path = self.repaired_path_edit.text()

        if not os.path.exists(raw_folder_path):
            self.show_message("Error", "RAW folder does not exist.")
            return

        # Create the Extracted Folder if it doesn't exist
        if not os.path.exists(repaired_folder_path):
            os.makedirs(repaired_folder_path)

        # Create the JPEG extraction worker and start the extraction process
        self.worker = JPEGExtractionWorker(raw_folder_path, repaired_folder_path)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_updated.connect(self.update_log)
        self.worker.extraction_finished.connect(self.extraction_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_box.append(message)

    def extraction_finished(self, message):
        self.show_message("Extraction Complete", message)

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)


class JPEGExtractionWorker(QThread):
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    extraction_finished = pyqtSignal(str)

    def __init__(self, raw_folder_path, repaired_folder_path):
        super().__init__()
        self.raw_folder_path = raw_folder_path
        self.repaired_folder_path = repaired_folder_path

    def run(self):
        files = [os.path.join(self.raw_folder_path, file) for file in os.listdir(self.raw_folder_path) if
                 file.lower().endswith((".arw", ".cr2", ".cr3", ".nef", ".jpg"))]

        total_files = len(files)
        files_processed = 0

        for file in files:
            file_name = os.path.basename(file)
            self.log_updated.emit(f"Processing {file_name}...")
            extract_jpeg_from_raw(file, self.repaired_folder_path)
            self.log_updated.emit(f"{file_name} extracted.")
            files_processed += 1
            progress = (files_processed / total_files) * 100
            self.progress_updated.emit(progress)

        self.extraction_finished.emit("JPEG extraction process completed.")

def extract_jpeg_from_raw(raw_file_path, repaired_folder):
    with open(raw_file_path, 'rb') as raw_file:
        raw_data = raw_file.read()

        # Assuming the JPEG data is between the markers b'\xff\xd8\xff' and b'\xff\xd9'
        start_marker = b'\xff\xd8\xff'
        end_marker = b'\xff\xd9'

        start_index = raw_data.rfind(start_marker)
        end_index = raw_data.rfind(end_marker)

        if start_index != -1 and end_index != -1:
            # Extract the JPEG data
            jpeg_data = raw_data[start_index:end_index + 2]

            # Extract base filename without the extension
            raw_file_name, _ = os.path.splitext(os.path.basename(raw_file_path))
            base_file_name = raw_file_name.split('.')[0]

            # Save the extracted JPEG data to a new file with the same base name as RAW but with .JPG extension
            jpeg_file_path = os.path.join(repaired_folder, base_file_name + ".JPG")
            with open(jpeg_file_path, 'wb') as jpeg_file:
                jpeg_file.write(jpeg_data)

            print(f"JPEG data extracted from '{raw_file_path}' and saved to '{jpeg_file_path}'.")
        else:
            print(f"No JPEG data found in '{raw_file_path}'.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = JPEGRepairApp()
    window.show()
    sys.exit(app.exec())
