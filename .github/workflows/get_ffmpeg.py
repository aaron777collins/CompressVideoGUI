#!/usr/bin/env python3
"""
Download a recent static ffmpeg + ffprobe for the given GitHub runner OS and
place them under externals/<platform>/ so PyInstaller can bundle them.

Called from the workflow step as:
    python get_ffmpeg.py Windows   | macOS | Linux
"""
from __future__ import annotations
import sys, os, zipfile, tarfile, shutil, tempfile, urllib.request, pathlib, stat

# ---------------------------------------------------------------------------
TARGET = sys.argv[1]  # "Windows" | "macOS" | "Linux"

if TARGET == "Windows":
    URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    BIN_NAMES = ["ffmpeg.exe", "ffprobe.exe"]
    DEST = pathlib.Path("externals/windows")
elif TARGET == "macOS":
    URL = "https://evermeet.cx/ffmpeg/getrelease/zip"
    BIN_NAMES = ["ffmpeg", "ffprobe"]
    DEST = pathlib.Path("externals/macos")
elif TARGET == "Linux":
    URL = "https://johnvansickle.com/ffmpeg/old-releases/ffmpeg-6.1-amd64-static.tar.xz"
    BIN_NAMES = ["ffmpeg", "ffprobe"]
    DEST = pathlib.Path("externals/linux")
else:
    sys.exit(f"Unknown target '{TARGET}'")

DEST.mkdir(parents=True, exist_ok=True)
print(f"Fetching static build for {TARGET} ...")

# ---------------------------------------------------------------------------

fd, tmp_archive = tempfile.mkstemp(suffix=URL.rsplit("/", 1)[-1])
os.close(fd)
urllib.request.urlretrieve(URL, tmp_archive)

def wants(file_path: str) -> bool:
    """Return True if the basename matches one of BIN_NAMES."""
    return pathlib.Path(file_path).name in BIN_NAMES

def save_to_dest(stream, name: str) -> None:
    out_path = DEST / name
    with open(out_path, "wb") as dst:
        shutil.copyfileobj(stream, dst)
    # make executable (best‑effort on Windows)
    try:
        os.chmod(out_path, os.stat(out_path).st_mode | stat.S_IEXEC)
    except OSError:
        pass

if tmp_archive.endswith(".zip"):
    with zipfile.ZipFile(tmp_archive) as z:
        for member in z.infolist():
            if member.is_dir():
                continue
            if wants(member.filename):
                with z.open(member) as src:
                    save_to_dest(src, pathlib.Path(member.filename).name)
else:  # tar.*
    with tarfile.open(tmp_archive) as t:
        for member in t.getmembers():
            if not member.isfile():
                continue
            if wants(member.name):
                with t.extractfile(member) as src:
                    save_to_dest(src, pathlib.Path(member.name).name)

os.remove(tmp_archive)
print(f"ffmpeg + ffprobe saved to {DEST}")
