import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QFileDialog, QSlider, QLabel, QHBoxLayout, QCheckBox, QComboBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer
from pyo import Server, SfPlayer, SndTable, Freeverb

class ReverbControlWidget(QWidget):
    """
    """
    def __init__(self, parent_track):
        super().__init__()
        self.parent_track = parent_track
        layout = QVBoxLayout()

        # Size slider.
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(0, 100)
        self.size_slider.setValue(80)
        self.size_slider.valueChanged.connect(self.parameters_changed)
        layout.addWidget(QLabel("Size"))
        layout.addWidget(self.size_slider)

        # Damp slider.
        self.damp_slider = QSlider(Qt.Orientation.Horizontal)
        self.damp_slider.setRange(0, 100)
        self.damp_slider.setValue(70)
        self.damp_slider.valueChanged.connect(self.parameters_changed)
        layout.addWidget(QLabel("Damp"))
        layout.addWidget(self.damp_slider)

        # Balance slider.
        self.bal_slider = QSlider(Qt.Orientation.Horizontal)
        self.bal_slider.setRange(0, 100)
        self.bal_slider.setValue(50)
        self.bal_slider.valueChanged.connect(self.parameters_changed)
        layout.addWidget(QLabel("Wet/Dry"))
        layout.addWidget(self.bal_slidert)

        self.setLayout(layout)

    def parameters_changed(self):
        """
        Called when any slider value changes.
        Update the reverb effect if it's active.
        """
        self.parent_track.update_reverb_params()

    def get_values(self):
        """
        Returns the current values as floats in a normalized range (0.0 to 1.0).
        """
        size = self.size_slider.value() / 100.0
        damp = self.damp_slider.value() / 100.0
        bal = self.bal_slider.value() / 100.0
        return size, damp, bal

class TrackWidget(QWidget):
    def __init__(self, track_name="Track", app=None):
        super().__init__()
        self.app = app  # Reference to the main AudioPlayerApp.
        self.track_name = track_name
        self.file_path = None
        self.file_duration = 0.0  # Duration in seconds.
        self.player = None
        self.effect = None  # Store the current processed effect.
        self.playing = False
        self.offset = 0.0  # Playback start offset (seconds).
        self.start_time = 0.0  # Time when playback started.
        self.seeking = False  # Flag to indicate slider dragging.

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

        # Position Slider.
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMinimum(0)
        self.position_slider.setMaximum(1000)  # Will be updated when a file is loaded.
        self.position_slider.sliderPressed.connect(self.on_slider_pressed)
        self.position_slider.sliderReleased.connect(self.on_slider_released)
        layout.addWidget(QLabel("Position", self, styleSheet="color: white;"))
        layout.addWidget(self.position_slider)

        # Effects Selector.
        self.effect_combo = QComboBox()
        self.effect_combo.addItem("None")
        self.effect_combo.addItem("Reverb")
        self.effect_combo.currentIndexChanged.connect(self.update_effect_chain)
        layout.addWidget(QLabel("Effect", self, styleSheet="color: white;"))
        layout.addWidget(self.effect_combo)

        # Effect Parameters Panel.
        self.effect_params_widget = QStackedWidget()
        # Page 0: Empty widget for "None".
        self.effect_params_widget.addWidget(QWidget())
        # Page 1: Reverb control widget.
        self.reverb_controls = ReverbControlWidget(self)
        self.effect_params_widget.addWidget(self.reverb_controls)
        layout.addWidget(self.effect_params_widget)

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
            tbl = SndTable(file_path)
            self.file_duration = tbl.getDur()  # Duration in seconds.
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
        if self.app and self.app.sync_checkbox.isChecked():
            self.app.sync_play(start=True)
            return

        if not self.playing:
            self.start_from_offset(self.offset)
        else:
            self.pause_playback()

    def start_from_offset(self, offset_val):
        volume = self.volume_slider.value() / 100.0
        self.player = SfPlayer(
            self.file_path, speed=1, loop=False,
            mul=volume, offset=offset_val
        )
        # Apply the chosen effect.
        self.effect = self.get_processed_output(self.player)
        self.effect.out()
        self.start_time = time.time()
        self.playing = True
        self.play_button.setText("Stop")
        self.timer.start(50)

    def pause_playback(self):
        if self.player is not None:
            self.player.stop()
        self.offset += time.time() - self.start_time
        self.playing = False
        self.play_button.setText("Play")
        self.timer.stop()

    def update_position(self):
        if self.playing and not self.seeking:
            elapsed = time.time() - self.start_time
            current_pos = self.offset + elapsed
            if current_pos >= self.file_duration:
                self.position_slider.setValue(int(self.file_duration * 1000))
                if self.player is not None:
                    self.player.stop()
                self.playing = False
                self.play_button.setText("Play")
                self.timer.stop()
                self.offset = 0.0
            else:
                self.position_slider.setValue(int(current_pos * 1000))

    def on_slider_pressed(self):
        self.seeking = True

    def on_slider_released(self):
        self.seeking = False
        self.process_seek()

    def process_seek(self):
        if not self.file_path:
            return
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
            self.effect = self.get_processed_output(self.player)
            self.effect.out()
            self.start_time = time.time()
        if self.app and self.app.sync_checkbox.isChecked():
            self.app.sync_seek(new_pos, origin=self)

    def update_volume(self):
        if self.player is not None:
            new_volume = self.volume_slider.value() / 100.0
            self.player.mul = new_volume

    def get_processed_output(self, raw_signal):
        """
        Returns the processed output based on the effect selected.
        """
        effect = self.effect_combo.currentText()
        if effect == "Reverb":
            # Read parameter values from the reverb controls.
            size, damp, bal = self.reverb_controls.get_values()
            return Freeverb(raw_signal, size=size, damp=damp, bal=bal)
        else:
            return raw_signal

    def update_effect_chain(self):
        """
        Called when the effect selection changes.
        Switch the parameters panel and reapply the effect chain.
        """
        effect = self.effect_combo.currentText()
        if effect == "Reverb":
            self.effect_params_widget.setCurrentIndex(1)
        else:
            self.effect_params_widget.setCurrentIndex(0)

        if self.playing:
            current_pos = self.offset + (time.time() - self.start_time)
            self.pause_playback()
            self.start_from_offset(current_pos)

    def update_reverb_params(self):
        """
        Called from the reverb controls when a parameter changes.
        If the track is playing and the current effect is reverb,
        update the parameters of the Freeverb object.
        """
        if self.effect_combo.currentText() == "Reverb" and self.effect is not None:
            # Re-read parameter values.
            size, damp, bal = self.reverb_controls.get_values()
            # Update Freeverb parameters directly.
            self.effect.size = size
            self.effect.damp = damp
            self.effect.bal = bal

class AudioPlayerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Song Remastering App")
        self.setGeometry(100, 100, 1200, 300)

        self.tracks = []

        main_layout = QVBoxLayout()

        # Global Controls at the Top.
        top_layout = QHBoxLayout()
        self.play_all_button = QPushButton("Play All")
        self.play_all_button.setStyleSheet("color: white;")
        self.play_all_button.clicked.connect(self.global_play_pause)
        top_layout.addWidget(self.play_all_button)

        self.sync_checkbox = QCheckBox("Sync Tracks")
        self.sync_checkbox.setStyleSheet("color: white;")
        top_layout.addWidget(self.sync_checkbox)

        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # Tracks layout.
        tracks_layout = QHBoxLayout()
        self.track1 = TrackWidget("Track 1", app=self)
        self.track2 = TrackWidget("Track 2", app=self)
        self.track3 = TrackWidget("Track 3", app=self)
        self.track4 = TrackWidget("Track 4", app=self)
        self.tracks = [self.track1, self.track2, self.track3, self.track4]

        tracks_layout.addWidget(self.track1)
        tracks_layout.addWidget(self.track2)
        tracks_layout.addWidget(self.track3)
        tracks_layout.addWidget(self.track4)
        main_layout.addLayout(tracks_layout)

        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")

    def global_play_pause(self):
        if any(track.playing for track in self.tracks):
            self.sync_play(start=False)
        else:
            self.sync_play(start=True)

    def sync_play(self, start=True):
        if start:
            for track in self.tracks:
                if track.file_path:
                    track.offset = 0.0
                    track.start_from_offset(0.0)
            self.play_all_button.setText("Pause All")
        else:
            for track in self.tracks:
                if track.playing:
                    track.pause_playback()
            self.play_all_button.setText("Play All")

    def sync_seek(self, new_pos, origin=None):
        for track in self.tracks:
            if track is origin:
                continue
            if track.file_path:
                if track.playing:
                    track.player.stop()
                track.offset = new_pos
                if origin.playing:
                    volume = track.volume_slider.value() / 100.0
                    track.player = SfPlayer(
                        track.file_path, speed=1, loop=False,
                        mul=volume, offset=new_pos
                    )
                    processed = track.get_processed_output(track.player)
                    processed.out()
                    track.start_time = time.time()
                    track.playing = True
                    track.play_button.setText("Stop")
        if origin and origin.playing:
            self.play_all_button.setText("Pause All")
        else:
            self.play_all_button.setText("Play All")

if __name__ == "__main__":
    s = Server().boot()
    s.start()

    app = QApplication(sys.argv)
    window = AudioPlayerApp()
    window.show()
    sys.exit(app.exec())
