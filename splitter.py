import asyncio
import os
import subprocess
from pydub import AudioSegment

import torch
from demucs import pretrained
from demucs.apply import apply_model
import torchaudio
from spleeter.separator import Separator

from utils import cache_file, get_cache_dir

def convert_audio(file_path: str) -> str:
    """Checks if a file is a .wav or .mp3, the only supported file formats from Demucs and Spleeter"""
    SUPPORTED_FORMATS = {".mp3", ".wav"}
    ext = os.path.splitext(file_path)[1].lower()
    if ext in SUPPORTED_FORMATS:
        return cache_file(file_path)
    else:
        cache_dir = get_cache_dir()
        # Save converted file into the cache folder.
        cached_file = os.path.join(cache_dir, os.path.splitext(os.path.basename(file_path))[0] + ".wav")
        if not os.path.exists(cached_file):
            print(f"Converting {file_path} to WAV format...")
            audio = AudioSegment.from_file(file_path)
            audio.export(cached_file, format="wav")
        return cached_file


async def spleeter_split(file_path: str, output_dir: str = None) -> tuple:
    """Splits a song into stems using Spleeter and caches the result."""
    from utils import get_cache_dir
    if output_dir is None:
        output_dir = os.path.join(get_cache_dir(), "Spleeter_Output")
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    track_folder = os.path.join(output_dir, base_name)
    expected_tracks = ("vocals.wav", "drums.wav", "bass.wav", "other.wav")

    #Check if exists
    if os.path.isdir(track_folder) and all(os.path.exists(os.path.join(track_folder, t)) for t in expected_tracks):
        print(f"Cache hit: Using previously split files from {track_folder}")
        return tuple(os.path.join(track_folder, t) for t in expected_tracks)

    #Was not in cache; start actually splitting
    print("Cache miss: Running Spleeter splitting process...")
    separator = Separator("spleeter:4stems")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, separator.separate_to_file, file_path, output_dir)

    return tuple(os.path.join(track_folder, t) for t in expected_tracks)


async def demucs_split(file_path: str, output_dir: str = None) -> tuple:
    """Splits a song into stems using Demucs and caches the result."""
    if output_dir is None:
        output_dir = os.path.join(get_cache_dir(), "Demucs_Output")
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    song_output_folder = os.path.join(output_dir, "htdemucs", base_name)
    stem_files = ("bass.wav", "drums.wav", "other.wav", "vocals.wav")

    # Check if the output folder exists with all required stem files.
    if os.path.isdir(song_output_folder) and all(
            os.path.exists(os.path.join(song_output_folder, s)) for s in stem_files):
        print(f"Cache hit: Using previously split files from {song_output_folder}")
        return tuple(os.path.join(song_output_folder, s) for s in stem_files)

    # Otherwise, perform the Demucs splitting.
    print("Cache miss: Running Demucs splitting process...")
    process = await asyncio.create_subprocess_exec(
        "demucs", "--out", output_dir, file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Demucs failed:\n{stderr.decode()}")

    # Return the new expected path
    return tuple(os.path.join(song_output_folder, s) for s in stem_files)

# JUST FOR DEBUGGING BELOW
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


#C:/Users/Atlas/Music/converted_audio.wav