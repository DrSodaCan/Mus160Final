# utils.py
import os
import platform
import shutil

def get_cache_dir():
    """Return a folder for caching song data, depending on the OS."""
    system = platform.system()
    if system == "Windows":
        base_dir = os.environ.get('APPDATA', os.path.expanduser("~"))
        cache_dir = os.path.join(base_dir, "SongRemasteringCache")
    elif system == "Darwin": #Mac
        cache_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "SongRemasteringCache")
    else:  # Linux and others.
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "SongRemasteringCache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def cache_file(file_path: str) -> str:
    """Copy the file into the OS-specific cache folder (if not already there) and return the cached path."""
    cache_dir = get_cache_dir()
    base_name = os.path.basename(file_path)
    cached_file = os.path.join(cache_dir, base_name)
    # Copy if file is not already cached.
    if not os.path.exists(cached_file):
        shutil.copy2(file_path, cached_file)
    return cached_file
