#!/usr/bin/env python3
"""
Download a recent static ffmpeg + ffprobe for the given GitHub OS and drop them
under externals/<platform>/ so PyInstaller can bundle them.

Invoked from the workflow as:
    python get_ffmpeg.py Windows
    python get_ffmpeg.py macOS
    python get_ffmpeg.py Linux
"""
import sys, os, zipfile, tarfile, shutil, tempfile, urllib.request, pathlib, platform, subprocess, json, re

TARGET = sys.argv[1]  # "Windows" | "macOS" | "Linux"

# ------------------------ choose URLs ---------------------------------------
if TARGET == "Windows":
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    bin_names = ["ffmpeg.exe", "ffprobe.exe"]
    dest_dir = pathlib.Path("externals/windows")
elif TARGET == "macOS":
    url = "https://evermeet.cx/ffmpeg/getrelease/zip"
    bin_names = ["ffmpeg", "ffprobe"]
    dest_dir = pathlib.Path("externals/macos")
elif TARGET == "Linux":
    url = "https://johnvansickle.com/ffmpeg/old-releases/ffmpeg-6.1-amd64-static.tar.xz"
    bin_names = ["ffmpeg", "ffprobe"]
    dest_dir = pathlib.Path("externals/linux")
else:
    sys.exit(f"Unknown target {TARGET}")

dest_dir.mkdir(parents=True, exist_ok=True)

# ------------------------ download & extract --------------------------------
print(f"⬇  Fetching static build for {TARGET} …")
fd, tmp_archive = tempfile.mkstemp(suffix=url.split("/")[-1])
os.close(fd)
urllib.request.urlretrieve(url, tmp_archive)

def pick(member):
    return any(member.name.endswith(b) or member.name.endswith("/" + b) for b in bin_names)

if tmp_archive.endswith(".zip"):
    with zipfile.ZipFile(tmp_archive) as z:
        for m in z.infolist():
            if pick(m):
                out = dest_dir / pathlib.Path(m.filename).name
                with z.open(m) as src, open(out, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                out.chmod(0o755)
else:  # tar.*
    with tarfile.open(tmp_archive) as t:
        for m in t.getmembers():
            if pick(m):
                out = dest_dir / pathlib.Path(m.name).name
                with t.extractfile(m) as src, open(out, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                out.chmod(0o755)

os.remove(tmp_archive)
print(f"✅  ffmpeg + ffprobe saved to {dest_dir}")
