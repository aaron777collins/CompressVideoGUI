#!/usr/bin/env python3
"""
Fetch ffmpeg + ffprobe for the given GitHub runner OS and copy them to
externals/<os>/ so PyInstaller can bundle them.

Usage from CI:
    python get_ffmpeg.py Windows | macOS | Linux
"""
from __future__ import annotations
import sys, os, zipfile, tarfile, shutil, tempfile, urllib.request, pathlib, stat

TARGET = sys.argv[1]   # GitHub runner OS string

# ---------------------------------------------------------------------------
def save_to_dest(stream, dest_dir: pathlib.Path, name: str):
    dest = dest_dir / name
    with open(dest, "wb") as f:
        shutil.copyfileobj(stream, f)
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC)  # add +x

# ---------------------------------------------------------------------------
if TARGET == "Windows":
    URLS = ["https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"]
    BIN_NAMES = ["ffmpeg.exe", "ffprobe.exe"]
    DEST = pathlib.Path("externals/windows")

elif TARGET == "macOS":
    # Two separate ZIPs: one for ffmpeg, one for ffprobe
    URLS = [
        "https://evermeet.cx/ffmpeg/getrelease/zip",
        "https://evermeet.cx/ffprobe/getrelease/zip",
    ]
    BIN_NAMES = ["ffmpeg", "ffprobe"]
    DEST = pathlib.Path("externals/macos")

elif TARGET == "Linux":
    # Use distro ffmpeg already installed via apt and copy it.
    BIN_NAMES = ["ffmpeg", "ffprobe"]
    DEST = pathlib.Path("externals/linux")
    DEST.mkdir(parents=True, exist_ok=True)
    for tool in BIN_NAMES:
        src = shutil.which(tool)
        if not src:
            sys.exit(f"{tool} not found on Linux runner")
        shutil.copy(src, DEST / tool)
        os.chmod(DEST / tool, 0o755)
    print(f"Copied system ffmpeg & ffprobe → {DEST}")
    sys.exit(0)

else:
    sys.exit(f"Unknown target '{TARGET}'")

# ---------------- download & extract ---------------------------------------
DEST.mkdir(parents=True, exist_ok=True)
print(f"Fetching static build(s) for {TARGET} ...")

def want(path: str) -> bool:
    return pathlib.Path(path).name in BIN_NAMES

for url in URLS:
    fd, tmp_path = tempfile.mkstemp()
    os.close(fd)
    urllib.request.urlretrieve(url, tmp_path)

    if zipfile.is_zipfile(tmp_path):
        with zipfile.ZipFile(tmp_path) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                if want(info.filename):
                    with z.open(info) as src:
                        save_to_dest(src, DEST, pathlib.Path(info.filename).name)
    else:
        with tarfile.open(tmp_path) as t:
            for member in t.getmembers():
                if not member.isfile():
                    continue
                if want(member.name):
                    with t.extractfile(member) as src:
                        save_to_dest(src, DEST, pathlib.Path(member.name).name)

    os.remove(tmp_path)

print(f"ffmpeg & ffprobe saved to {DEST}")
