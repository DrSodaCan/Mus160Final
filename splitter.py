# splitter.py
import asyncio
import os
from spleeter.separator import Separator
from pydub import AudioSegment
import subprocess
import torch
from demucs import pretrained
from demucs.apply import apply_model
import torchaudio

# Import caching helpers.
from utils import cache_file, get_cache_dir

# Optional: Configure TensorFlow GPU memory growth to prevent memory issues.
try:
    import tensorflow as tf

    gpus = tf.config.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print("[TensorFlow] Memory growth enabled for GPUs.")
except Exception as e:
    print(f"[TensorFlow] Could not set memory growth: {e}")


def convert_audio(file_path: str) -> str:
    """
    Converts the input audio file to WAV if necessary and caches it.
    """
    SUPPORTED_FORMATS = {".mp3", ".wav"}
    ext = os.path.splitext(file_path)[1].lower()
    if ext in SUPPORTED_FORMATS:
        return cache_file(file_path)  # Cache and return.
    else:
        cache_dir = get_cache_dir()
        cached_file = os.path.join(cache_dir, os.path.splitext(os.path.basename(file_path))[0] + ".wav")
        if not os.path.exists(cached_file):
            print(f"Converting {file_path} to WAV format...")
            audio = AudioSegment.from_file(file_path)
            audio.export(cached_file, format="wav")
        return cached_file


async def spleeter_split(file_path: str, output_dir: str = None) -> tuple:
    """
    Splits a song into stems using Spleeter and saves output in the cache.
    Modifications include an explicit filename format to ensure proper splitting.
    """
    # Determine the output directory within the cache.
    if output_dir is None:
        output_dir = os.path.join(get_cache_dir(), "Spleeter_Output")
    os.makedirs(output_dir, exist_ok=True)

    print(f"[Spleeter] Splitting file: {file_path}")
    print(f"[Spleeter] Output directory: {output_dir}")

    # Create the Spleeter separator object for 4 stems.
    separator = Separator("spleeter:4stems")
    loop = asyncio.get_event_loop()

    # Run the separation function in an executor.
    # The lambda allows us to pass additional keyword arguments.
    await loop.run_in_executor(
        None,
        lambda: separator.separate_to_file(
            file_path,
            output_dir,
            codec="wav",
            filename_format="{filename}/{instrument}.{codec}"
        )
    )

    # Construct the expected output folder and files.
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    track_folder = os.path.join(output_dir, base_name)
    expected_tracks = ("vocals.wav", "drums.wav", "bass.wav", "other.wav")

    # Debugging: list the files in the track folder.
    if os.path.exists(track_folder):
        print("[Spleeter] Files in output folder:")
        for f in os.listdir(track_folder):
            print("  -", f)
    else:
        print(f"[Spleeter] ERROR: Expected track folder not found: {track_folder}")

    # Build the tuple of track paths.
    track_paths = []
    for track in expected_tracks:
        path = os.path.join(track_folder, track)
        if not os.path.exists(path):
            print(f"[Spleeter] WARNING: Expected track file not found: {path}")
        track_paths.append(path)

    return tuple(track_paths)


async def demucs_split(file_path: str, output_dir: str = None) -> tuple:
    """
    Splits a song into stems using Demucs and saves output in the cache.
    """
    # Use a cache folder subdirectory for Demucs output.
    if output_dir is None:
        output_dir = os.path.join(get_cache_dir(), "Demucs_Output")
    os.makedirs(output_dir, exist_ok=True)

    process = await asyncio.create_subprocess_exec(
        "demucs", "--out", output_dir, file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Demucs failed:\n{stderr.decode()}")

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    song_output_folder = os.path.join(output_dir, base_name)
    stem_files = ("bass.wav", "drums.wav", "other.wav", "vocals.wav")
    stem_paths = tuple(os.path.join(song_output_folder, stem) for stem in stem_files)
    return stem_paths


# Debugging main (for testing purposes):
if __name__ == "__main__":
    async def main():
        file_path = input("Enter the path to the audio file: ").strip()
        method = input("Choose separation method (spleeter/demucs): ").strip().lower()

        converted_file = convert_audio(file_path)
        print("Converted file ready:", converted_file)
        if method == "spleeter":
            stems = await spleeter_split(converted_file)
        elif method == "demucs":
            stems = await demucs_split(converted_file)
        else:
            print("Invalid method chosen.")
            return

        print("Separated stem files:")
        for path in stems:
            print(path)


    asyncio.run(main())

#C:/Users/Atlas/Music/converted_audio.wav