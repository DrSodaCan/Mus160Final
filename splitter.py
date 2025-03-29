import asyncio
import os
import subprocess
from spleeter.separator import Separator
from pydub import AudioSegment

import torch
from pydub import AudioSegment
from demucs import pretrained
from demucs.apply import apply_model
import torchaudio

def convert_audio(file_path: str) -> str:
    """ Converts the input audio file to WAV if it's not in MP3 or WAV format. """
    SUPPORTED_FORMATS = {".mp3", ".wav"}
    CONVERTED_FILE = "converted_audio.wav"

    ext = os.path.splitext(file_path)[1].lower()
    if ext in SUPPORTED_FORMATS:
        return file_path  # No conversion needed

    print(f"Converting {file_path} to WAV format...")
    audio = AudioSegment.from_file(file_path)
    audio.export(CONVERTED_FILE, format="wav")
    return CONVERTED_FILE


async def spleeter_split(file_path: str, output_dir: str = "output") -> tuple:
    """ Splits a song into stems using Spleeter. """
    os.makedirs(output_dir, exist_ok=True)
    separator = Separator("spleeter:4stems")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, separator.separate_to_file, file_path, output_dir)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    track_folder = os.path.join(output_dir, base_name)
    expected_tracks = ("vocals.wav", "drums.wav", "bass.wav", "other.wav")
    track_paths = tuple(os.path.join(track_folder, track) for track in expected_tracks)

    return track_paths


async def demucs_split(file_path: str, output_dir: str = "separated") -> tuple:
    """ Splits a song into stems using Demucs. """
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

####JUST FOR DEBUGGING BELOW
async def main():
    file_path = input("Enter the path to the audio file: ").strip()
    method = input("Choose separation method (spleeter/demucs): ").strip().lower()

    converted_file = convert_audio(file_path)
    print("File ready")
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


if __name__ == "__main__":
    asyncio.run(main())

    #C:/Users/AtlasG/Music/Garasudama.flac
    #C:/Users/AtlasG/Music/converted_audio.wav