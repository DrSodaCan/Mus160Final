import os
import sys
import platform
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QLabel, QComboBox
from splitter import split_song, get_appdata_folder

class StemSplitterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Audio Stem Splitter")
        self.setGeometry(100, 100, 400, 250)

        layout = QVBoxLayout()

        self.label = QLabel("Select an audio file:", self)
        layout.addWidget(self.label)

        self.btnBrowse = QPushButton("Browse", self)
        self.btnBrowse.clicked.connect(self.browseFile)
        layout.addWidget(self.btnBrowse)

        self.methodSelector = QComboBox(self)
        self.methodSelector.addItems(["Demucs (High Accuracy)", "Spleeter (Faster)"])
        layout.addWidget(self.methodSelector)

        self.btnSplit = QPushButton("Split Song", self)
        self.btnSplit.clicked.connect(self.splitSong)
        layout.addWidget(self.btnSplit)

        self.btnOpenFolder = QPushButton("View Stems Folder", self)
        self.btnOpenFolder.clicked.connect(self.openOutputFolder)
        layout.addWidget(self.btnOpenFolder)

        self.statusLabel = QLabel("", self)
        layout.addWidget(self.statusLabel)

        self.setLayout(layout)
        self.audioFile = ""

    def browseFile(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open Audio File", "", "Audio Files (*.mp3 *.wav *.flac)")
        if file_path:
            self.audioFile = file_path
            self.label.setText(f"Selected: {file_path}")
            file_path = r"C:/Users/Atlas/Downloads/Von (Outer Echo Mix).mp3"

            if os.path.exists(file_path):
                print("File exists!")
            else:
                print("File not found.")

    def splitSong(self):
        if not self.audioFile:
            self.statusLabel.setText("Please select a file first.")
            return

        method = "demucs" if "Demucs" in self.methodSelector.currentText() else "spleeter"

        try:
            self.statusLabel.setText("Processing... Please wait.")
            stem_paths = split_song(self.audioFile, method)
            self.statusLabel.setText("Split complete! Stems saved at:\n" + "\n".join(stem_paths))
        except Exception as e:
            self.statusLabel.setText(f"Error: {str(e)}")

    def openOutputFolder(self):
        """Opens the AppData folder where stems are stored."""
        folder_path = str(get_appdata_folder())

        if platform.system() == "Windows":
            subprocess.run(["explorer", folder_path], shell=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        else:  # Linux
            subprocess.run(["xdg-open", folder_path])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = StemSplitterApp()
    ex.show()
    sys.exit(app.exec())

