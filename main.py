import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                             QFileDialog, QSlider, QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading


class TrackWidget(QWidget):
    def __init__(self, track_name="Track"):
        super().__init__()
        self.track_name = track_name
        self.audio_data = None
        self.samplerate = None
        self.playing = False
        self.current_frame = 0

        self.setStyleSheet("background-color: #121212; border-radius: 10px; padding: 10px;")
        layout = QVBoxLayout()

        # Track Name Label
        self.label = QLabel(track_name)
        self.label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(self.label)

        # File Select Button
        self.select_button = QPushButton("Select File")
        self.select_button.setStyleSheet("color: white;")
        self.select_button.clicked.connect(self.load_file)
        layout.addWidget(self.select_button)

        # Play Button
        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet("color: white;")
        self.play_button.clicked.connect(self.toggle_playback)
        layout.addWidget(self.play_button)

        # Volume Slider
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.valueChanged.connect(self.update_volume)
        layout.addWidget(QLabel("Volume", self, styleSheet="color: white;"))
        layout.addWidget(self.volume_slider)

        # Position Slider
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMinimum(0)
        self.position_slider.setMaximum(100)
        self.position_slider.sliderReleased.connect(self.seek_audio)
        layout.addWidget(QLabel("Position", self, styleSheet="color: white;"))
        layout.addWidget(self.position_slider)

        self.setLayout(layout)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.audio_data, self.samplerate = sf.read(file_path, dtype='float32')
            self.position_slider.setMaximum(len(self.audio_data))

    def toggle_playback(self):
        if self.audio_data is not None:
            if not self.playing:
                self.playing = True
                self.play_button.setText("Stop")
                self.timer.start(100)
                threading.Thread(target=self.play_audio, daemon=True).start()
            else:
                self.playing = False
                self.play_button.setText("Play")
                sd.stop()
                self.timer.stop()

    def play_audio(self):
        volume = self.volume_slider.value() / 100.0
        data = (self.audio_data * volume).astype(np.float32)
        self.current_frame = 0
        sd.play(data[self.current_frame:], self.samplerate)
        sd.wait()
        self.playing = False
        self.play_button.setText("Play")
        self.timer.stop()

    def update_position(self):
        if self.playing:
            self.current_frame += self.samplerate // 10
            if self.current_frame >= len(self.audio_data):
                self.current_frame = len(self.audio_data)
                self.toggle_playback()
            self.position_slider.setValue(self.current_frame)

    def seek_audio(self):
        if self.audio_data is not None:
            self.current_frame = self.position_slider.value()
            sd.stop()
            self.toggle_playback()

    def update_volume(self):
        if self.audio_data is not None and self.playing:
            sd.stop()
            self.toggle_playback()


class AudioPlayerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Song Remastering App")
        self.setGeometry(100, 100, 800, 300)

        layout = QHBoxLayout()  # Change from QVBoxLayout to QHBoxLayout

        self.track1 = TrackWidget("Vocals")
        self.track2 = TrackWidget("Drums")

        layout.addWidget(self.track1)
        layout.addWidget(self.track2)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioPlayerApp()
    window.show()
    sys.exit(app.exec())
