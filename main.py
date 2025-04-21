import sys
import os
import asyncio
import soundfile as sf
import numpy as np
import sounddevice as sd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QSlider, QHBoxLayout, QComboBox,
    QFormLayout, QSpacerItem, QSizePolicy, QCheckBox,
    QDialog, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from pedalboard import Pedalboard, Reverb, Delay
from splitter import convert_audio, spleeter_split, demucs_split


class Track(QWidget):
    def __init__(self, track_number, sync_callback=None, get_sync_state=None):
        super().__init__()
        self.track_number = track_number
        self.sync_callback = sync_callback
        self.get_sync_state = get_sync_state
        self.original_audio_data = None
        self.audio_data = None
        self.sample_rate = None
        self.stream = None
        self.is_playing = False
        self.position = 0
        self.effect_params = {}
        self.board = Pedalboard([])

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.label = QLabel(f"Track {self.track_number}: No file loaded")
        layout.addWidget(self.label)

        self.import_button = QPushButton('Import')
        self.import_button.clicked.connect(self.import_audio)
        layout.addWidget(self.import_button)

        self.play_pause_button = QPushButton('Play')
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setEnabled(False)
        layout.addWidget(self.play_pause_button)

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel('Volume'))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        volume_layout.addWidget(self.volume_slider)
        layout.addLayout(volume_layout)

        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.seek_position)
        layout.addWidget(self.progress_slider)

        effects_layout = QFormLayout()
        self.effects_dropdown = QComboBox()
        self.effects_dropdown.addItems(["None", "Reverb", "Delay"])
        self.effects_dropdown.currentTextChanged.connect(self.effect_changed)
        effects_layout.addRow("Effects:", self.effects_dropdown)
        layout.addLayout(effects_layout)

        self.effects_options_layout = QFormLayout()
        layout.addLayout(self.effects_options_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)

        self.setLayout(layout)

    def import_audio(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Audio File", "", "Audio Files (*.wav *.mp3 *.flac)")
        if filename:
            self.load_audio(filename)

    def load_audio(self, filename: str):
        self.original_audio_data, self.sample_rate = sf.read(filename, always_2d=True)
        self.apply_effect()
        self.label.setText(f"Track {self.track_number}: {os.path.basename(filename)}")
        self.play_pause_button.setEnabled(True)

    def audio_callback(self, outdata, frames, time, status):
        if status:
            print(status)
        chunk = self.audio_data[self.position:self.position + frames]
        volume = self.volume_slider.value() / 100
        if len(chunk) < frames:
            outdata[:len(chunk)] = chunk * volume
            outdata[len(chunk):] = 0
            self.stop_audio()
            return
        outdata[:] = chunk * volume
        self.position += frames

    def toggle_play_pause(self):
        if self.get_sync_state and self.get_sync_state():
            if self.sync_callback:
                self.sync_callback(self)
        else:
            self.play_pause_audio()

    def play_pause_audio(self):
        if not self.is_playing:
            if self.position >= len(self.audio_data):
                self.position = 0
            self.stream = sd.OutputStream(samplerate=self.sample_rate,
                                          channels=self.audio_data.shape[1],
                                          callback=self.audio_callback)
            self.stream.start()
            self.play_pause_button.setText('Pause')
            self.timer.start(100)
            self.is_playing = True
        else:
            self.stop_audio()

    def stop_audio(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.timer.stop()
        self.play_pause_button.setText('Play')
        self.is_playing = False

    def update_progress(self):
        if self.audio_data is not None:
            progress = int((self.position / len(self.audio_data)) * 1000)
            self.progress_slider.setValue(progress)

    def seek_position(self, position):
        if self.audio_data is not None:
            new_pos = min(max(0, int((position / 1000) * len(self.audio_data))), len(self.audio_data) - 1)
            self.position = new_pos
            if self.get_sync_state and self.get_sync_state():
                if self.sync_callback:
                    self.sync_callback(self, seek_only=True)

    def effect_changed(self, effect_name):
        while self.effects_options_layout.count():
            item = self.effects_options_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.effect_params.clear()
        if effect_name == "Reverb":
            room_slider = QSlider(Qt.Orientation.Horizontal)
            room_slider.setRange(0, 100)
            room_slider.setValue(50)
            room_slider.valueChanged.connect(self.apply_effect)
            self.effects_options_layout.addRow("Room Size:", room_slider)
            self.effect_params['room_size'] = room_slider

        elif effect_name == "Delay":
            delay_slider = QSlider(Qt.Orientation.Horizontal)
            delay_slider.setRange(1, 2000)
            delay_slider.setValue(500)
            delay_slider.sliderReleased.connect(self.apply_effect)
            self.effects_options_layout.addRow("Delay (ms):", delay_slider)
            self.effect_params['delay_seconds'] = delay_slider

        self.apply_effect()

    def apply_effect(self):
        if self.original_audio_data is None:
            return

        effect_name = self.effects_dropdown.currentText()
        if effect_name == "Reverb":
            room_size = self.effect_params['room_size'].value() / 100
            self.board = Pedalboard([Reverb(room_size=room_size)])
        elif effect_name == "Delay":
            delay_seconds = self.effect_params['delay_seconds'].value() / 1000
            self.board = Pedalboard([Delay(delay_seconds=delay_seconds)])
        else:
            self.board = Pedalboard([])

        self.audio_data = self.board(self.original_audio_data.copy(), self.sample_rate)


class AudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.tracks = []
        self.sync_enabled = False
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        self.play_all_button = QPushButton("Play All Tracks")
        self.play_all_button.clicked.connect(self.play_all_tracks)
        control_layout.addWidget(self.play_all_button)

        self.add_track_button = QPushButton("Add Track")
        self.add_track_button.clicked.connect(self.add_new_track)
        control_layout.addWidget(self.add_track_button)

        self.sync_checkbox = QCheckBox("Sync Playback")
        self.sync_checkbox.stateChanged.connect(self.toggle_sync)
        control_layout.addWidget(self.sync_checkbox)

        self.splitter_button = QPushButton("Splitter")
        self.splitter_button.clicked.connect(self.open_splitter_dialog)
        control_layout.addWidget(self.splitter_button)

        self.export_button = QPushButton("Export Tracks")
        self.export_button.clicked.connect(self.export_tracks)
        control_layout.addWidget(self.export_button)

        main_layout.addLayout(control_layout)

        self.track_container = QHBoxLayout()
        main_layout.addLayout(self.track_container)

        for i in range(4):
            self.add_new_track()

        self.setLayout(main_layout)
        self.setWindowTitle('Multi-Track Audio Player with Pedalboard')
        self.resize(1200, 600)

    def add_new_track(self):
        track = Track(len(self.tracks) + 1, self.sync_playback, self.get_sync_state)
        self.tracks.append(track)
        self.track_container.addWidget(track)

    def get_sync_state(self):
        return self.sync_enabled

    def toggle_sync(self):
        self.sync_enabled = self.sync_checkbox.isChecked()

    def sync_playback(self, source_track, seek_only=False):
        for track in self.tracks:
            if track is source_track or track.audio_data is None:
                continue
            if seek_only:
                track.position = source_track.position
            else:
                if source_track.is_playing:
                    track.position = source_track.position
                    if not track.is_playing:
                        track.play_pause_audio()
                else:
                    if track.is_playing:
                        track.stop_audio()

    def play_all_tracks(self):
        for track in self.tracks:
            if track.audio_data is not None and not track.is_playing:
                track.play_pause_audio()

    def open_splitter_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Splitter")
        layout = QVBoxLayout()
        form = QFormLayout()

        file_layout = QHBoxLayout()
        self.split_file_path = QLineEdit()
        file_layout.addWidget(self.split_file_path)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self._browse_file())
        file_layout.addWidget(browse_btn)
        form.addRow("Input File:", file_layout)

        self.method_combo = QComboBox()
        self.method_combo.addItems(["Spleeter", "Demucs"])
        form.addRow("Method:", self.method_combo)

        layout.addLayout(form)
        split_btn = QPushButton("Split and Load")
        split_btn.clicked.connect(lambda: self.handle_split(dialog))
        layout.addWidget(split_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Audio File to Split", "", "Audio Files (*.wav *.mp3 *.flac)")
        if path:
            self.split_file_path.setText(path)

    def handle_split(self, dialog):
        file_path = self.split_file_path.text()
        method = self.method_combo.currentText().lower()
        if not file_path:
            QMessageBox.warning(self, "No File", "Please select an input audio file.")
            return
        dialog.accept()
        try:
            converted = convert_audio(file_path)
            if method == 'spleeter':
                stems = asyncio.run(spleeter_split(converted))
            else:
                stems = asyncio.run(demucs_split(converted))
            for i, track in enumerate(self.tracks[:4]):
                track.load_audio(stems[i])
        except Exception as e:
            QMessageBox.critical(self, "Error during splitting", str(e))

    def export_tracks(self):
        # Collect mixed audio
        mixed = None
        sr = None
        for track in self.tracks:
            if track.audio_data is None:
                continue
            data = track.audio_data.copy()
            # apply volume
            volume = track.volume_slider.value() / 100
            data *= volume
            if mixed is None:
                mixed = data
                sr = track.sample_rate
            else:
                # pad shorter arrays
                if data.shape[0] > mixed.shape[0]:
                    pad = np.zeros((data.shape[0] - mixed.shape[0], mixed.shape[1]))
                    mixed = np.vstack((mixed, pad))
                elif mixed.shape[0] > data.shape[0]:
                    pad = np.zeros((mixed.shape[0] - data.shape[0], data.shape[1]))
                    data = np.vstack((data, pad))
                mixed = mixed + data
        if mixed is None:
            QMessageBox.warning(self, "No Tracks", "No tracks loaded to export.")
            return
        # normalize
        max_val = np.max(np.abs(mixed))
        if max_val > 1:
            mixed = mixed / max_val
        # save
        save_path, _ = QFileDialog.getSaveFileName(self, "Export Mixed Track", "", "WAV Files (*.wav)")
        if save_path:
            sf.write(save_path, mixed, sr)
            QMessageBox.information(self, "Export Complete", f"Exported to {save_path}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AudioApp()
    window.show()
    sys.exit(app.exec())
