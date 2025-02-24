from PyQt6.QtCore import QObject, pyqtSignal


class SpleeterWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self, file_path):
        """
        Runs Spleeter on the given file path to split it into 4 stems.
        Emits finished with a dict of stems on success,
        or error with an error message on failure.
        """
        try:
            from spleeter.separator import Separator
            from spleeter.audio.adapter import AudioAdapter

            # Initialize separator for 4 stems
            separator = Separator("spleeter:4stems")
            audio_loader = AudioAdapter.default()

            # Load the audio file; sample_rate is forced to 44100 Hz for consistency
            waveform, _ = audio_loader.load(file_path, sample_rate=44100)

            # Perform separation; returns a dict with keys: vocals, drums, bass, other
            stems = separator.separate(waveform)
            self.finished.emit(stems)
        except Exception as e:
            self.error.emit(str(e))
