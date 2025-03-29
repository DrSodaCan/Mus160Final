import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QFileDialog, QSlider, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer

from pyo import Server, SfPlayer, SndTable


class TrackWidget(QWidget):
    def __init__(self, track_name="Track"):
        super().__init__()
        self.track_name = track_name
        self.file_path = None
        self.file_duration = 0.0  # Duration in seconds.
        self.player = None
        self.playing = False
        self.offset = 0.0  # Playback start offset (seconds).
        self.start_time = 0.0  # Time when playback started.

        self.setStyleSheet("background-color: #121212; border-radius: 10px; padding: 10px;")
        layout = QVBoxLayout()

        # Track Name Label.
        self.label = QLabel(track_name)
        self.label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(self.label)

        # File Select Button.
        self.select_button = QPushButton("Select File")
        self.select_button.setStyleSheet("color: white;")
        self.select_button.clicked.connect(self.load_file)
        layout.addWidget(self.select_button)

        # Play Button.
        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet("color: white;")
        self.play_button.clicked.connect(self.toggle_playback)
        layout.addWidget(self.play_button)

        # Volume Slider.
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.valueChanged.connect(self.update_volume)
        layout.addWidget(QLabel("Volume", self, styleSheet="color: white;"))
        layout.addWidget(self.volume_slider)

        # Position Slider (using milliseconds for smooth updates).
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMinimum(0)
        # Default maximum; will be updated when a file is loaded.
        self.position_slider.setMaximum(1000)
        self.position_slider.sliderReleased.connect(self.seek_audio)
        layout.addWidget(QLabel("Position", self, styleSheet="color: white;"))
        layout.addWidget(self.position_slider)

        self.setLayout(layout)

        # Timer to update slider position.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", "Audio Files (*.wav *.mp3)"
        )
        if file_path:
            self.file_path = file_path
            # Use SndTable to accurately get the duration.
            tbl = SndTable(file_path)
            self.file_duration = tbl.getDur()  # Duration in seconds.
            # Set slider maximum in milliseconds.
            self.position_slider.setMaximum(int(self.file_duration * 1000))
            self.offset = 0.0
            if self.player is not None:
                self.player.stop()
                self.player = None
            self.play_button.setText("Play")
            self.playing = False
            self.position_slider.setValue(0)

    def toggle_playback(self):
        if not self.file_path:
            return
        if not self.playing:
            # Start playback from the current offset.
            volume = self.volume_slider.value() / 100.0
            self.player = SfPlayer(
                self.file_path, speed=1, loop=False,
                mul=volume, offset=self.offset
            )
            self.player.out()
            self.start_time = time.time()
            self.playing = True
            self.play_button.setText("Stop")
            self.timer.start(50)
        else:
            # Stop playback and update offset.
            if self.player is not None:
                self.player.stop()
            self.offset += time.time() - self.start_time
            self.playing = False
            self.play_button.setText("Play")
            self.timer.stop()

    def update_position(self):
        if self.playing:
            elapsed = time.time() - self.start_time
            current_pos = self.offset + elapsed
            if current_pos >= self.file_duration:
                # When the end is reached, set slider to max and stop playback.
                self.position_slider.setValue(int(self.file_duration * 1000))
                if self.player is not None:
                    self.player.stop()
                self.playing = False
                self.play_button.setText("Play")
                self.timer.stop()
                self.offset = 0.0
                # Removed resetting slider to 0 so that slider remains at the end.
            else:
                self.position_slider.setValue(int(current_pos * 1000))

    def seek_audio(self):
        if not self.file_path:
            return
        # Slider value is in milliseconds.
        new_pos_ms = self.position_slider.value()
        new_pos = new_pos_ms / 1000.0
        self.offset = new_pos
        if self.playing:
            if self.player is not None:
                self.player.stop()
            volume = self.volume_slider.value() / 100.0
            self.player = SfPlayer(
                self.file_path, speed=1, loop=False,
                mul=volume, offset=self.offset
            )
            self.player.out()
            self.start_time = time.time()

    def update_volume(self):
        if self.player is not None:
            new_volume = self.volume_slider.value() / 100.0
            self.player.mul = new_volume


class AudioPlayerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Song Remastering App")
        self.setGeometry(100, 100, 1200, 300)

        # Use a vertical layout so we can add the "Play All" button.
        main_layout = QVBoxLayout()

        tracks_layout = QHBoxLayout()
        self.track1 = TrackWidget("Track 1")
        self.track2 = TrackWidget("Track 2")
        self.track3 = TrackWidget("Track 3")
        self.track4 = TrackWidget("Track 4")
        tracks_layout.addWidget(self.track1)
        tracks_layout.addWidget(self.track2)
        tracks_layout.addWidget(self.track3)
        tracks_layout.addWidget(self.track4)
        main_layout.addLayout(tracks_layout)

        # "Play All" Button.
        self.play_all_button = QPushButton("Play All")
        self.play_all_button.setStyleSheet("color: white;")
        self.play_all_button.clicked.connect(self.play_all_tracks)
        main_layout.addWidget(self.play_all_button)

        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")

    def play_all_tracks(self):
        # Iterate through each track and start playback if a file is loaded.
        for track in [self.track1, self.track2, self.track3, self.track4]:
            if track.file_path and not track.playing:
                track.toggle_playback()



if __name__ == "__main__":
    # Boot and start the pyo server.
    s = Server().boot()
    s.start()

    app = QApplication(sys.argv)
    window = AudioPlayerApp()
    window.show()
    sys.exit(app.exec())
