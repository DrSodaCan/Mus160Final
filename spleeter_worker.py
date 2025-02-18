# spleeter_worker.py

import traceback
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class SpleeterWorker(QObject):
    # Emitted when separation is complete. The dict maps stem names (e.g., 'vocals', 'drums', etc.) to NumPy arrays.
    finished = pyqtSignal(dict)
    # Emitted when an error occurs. The signal passes an error message.
    error = pyqtSignal(str)

    @pyqtSlot(str)
    def run(self, audio_file: str):
        """
        Accepts an audio file path, processes it with Spleeter to separate the stems,
        and emits the finished signal with a dictionary of separated stems.

        :param audio_file: The file path to the audio file.
        """
        try:
            # Import Spleeter's Separator here to ensure it's only imported when needed.
            from spleeter.separator import Separator

            # Initialize the separator for 4 stems. You can change this to 'spleeter:2stems', etc.
            separator = Separator('spleeter:4stems')

            # Perform separation. This returns a dictionary, e.g.,
            # {'vocals': np.array, 'drums': np.array, 'bass': np.array, 'other': np.array}
            stems = separator.separate(audio_file)

            # Emit the finished signal with the separated stems.
            self.finished.emit(stems)
        except Exception as e:
            # Capture the full traceback for debugging.
            tb = traceback.format_exc()
            self.error.emit(f"Error processing file:\n{str(e)}\n{tb}")

# Example usage (to be placed in your main module):
#
# from PyQt6.QtCore import QThread
# from spleeter_worker import SpleeterWorker
#
# def handle_finished(stems):
#     print("Separation complete!")
#     for stem, data in stems.items():
#         print(f"{stem}: {data.shape}")
#
# def handle_error(err_msg):
#     print("An error occurred:", err_msg)
#
# # Create the worker and a thread to run it.
# worker = SpleeterWorker()
# thread = QThread()
#
# # Move the worker to the thread.
# worker.moveToThread(thread)
#
# # Connect thread start to the worker's run method.
# thread.started.connect(lambda: worker.run("path/to/your/audiofile.wav"))
#
# # Connect worker signals to your handlers.
# worker.finished.connect(handle_finished)
# worker.error.connect(handle_error)
#
# # Start the thread.
# thread.start()
