#!/usr/bin/env python3
"""
Fetch ffmpeg + ffprobe for the given OS and copy them to externals/<os>/.

Called from CI like:
    python get_ffmpeg.py Windows | macOS | Linux
"""
from __future__ import annotations
import sys, os, zipfile, tarfile, shutil, tempfile, urllib.request, pathlib, stat, subprocess

TARGET = sys.argv[1]   # GitHub runner OS

# ---------------- choose download source -----------------------------------
if TARGET == "Windows":
    URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    BIN_NAMES = ["ffmpeg.exe", "ffprobe.exe"]
    DEST = pathlib.Path("externals/windows")

elif TARGET == "macOS":
    URL = "https://evermeet.cx/ffmpeg/getrelease/zip"   # returns a ZIP without '.zip' ext
    BIN_NAMES = ["ffmpeg", "ffprobe"]
    DEST = pathlib.Path("externals/macos")

elif TARGET == "Linux":
    # We already install the distro ffmpeg in the workflow, so just copy it.
    BIN_NAMES = ["ffmpeg", "ffprobe"]
    DEST = pathlib.Path("externals/linux")
    DEST.mkdir(parents=True, exist_ok=True)

    for tool in BIN_NAMES:
        src = shutil.which(tool)
        if not src:                 # defensive: should not happen
            sys.exit(f"{tool} not found on Linux runner")
        shutil.copy(src, DEST / tool)
        os.chmod(DEST / tool, 0o755)

    print(f"Copied system ffmpeg/ffprobe -> {DEST}")
    sys.exit(0)

else:
    sys.exit(f"Unknown target '{TARGET}'")

DEST.mkdir(parents=True, exist_ok=True)
print(f"Fetching static build for {TARGET} ...")

# ---------------- download & unpack ----------------------------------------
fd, tmp_path = tempfile.mkstemp()
os.close(fd)
urllib.request.urlretrieve(URL, tmp_path)

def want(path: str) -> bool:
    return pathlib.Path(path).name in BIN_NAMES

def save(stream, name: str):
    out = DEST / name
    with open(out, "wb") as dst:
        shutil.copyfileobj(stream, dst)
    out.chmod(out.stat().st_mode | stat.S_IEXEC)

if zipfile.is_zipfile(tmp_path):
    with zipfile.ZipFile(tmp_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            if want(info.filename):
                with zf.open(info) as src:
                    save(src, pathlib.Path(info.filename).name)
else:
    with tarfile.open(tmp_path) as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            if want(member.name):
                with tf.extractfile(member) as src:
                    save(src, pathlib.Path(member.name).name)

os.remove(tmp_path)
print(f"ffmpeg + ffprobe saved to {DEST}")
