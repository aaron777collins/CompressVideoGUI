#!/usr/bin/env python3
"""
Download static ffmpeg + ffprobe into externals/<os>/ so PyInstaller can bundle
them.  Called from CI with one argument (Windows | macOS | Linux).
"""
from __future__ import annotations
import sys, os, zipfile, tarfile, shutil, tempfile, urllib.request, pathlib, stat

TARGET = sys.argv[1]           # runner OS
DEST = pathlib.Path(f"externals/{TARGET.lower()}")  # windows / macos / linux
DEST.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
def save(stream, filename: str):
    out = DEST / filename
    with open(out, "wb") as f:
        shutil.copyfileobj(stream, f)
    out.chmod(out.stat().st_mode | stat.S_IEXEC)     # add +x even on macOS

def want(path: str, names: list[str]) -> bool:
    return pathlib.Path(path).name in names
# --------------------------------------------------------------------------

if TARGET == "Windows":
    ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    NAMES   = ["ffmpeg.exe", "ffprobe.exe"]
    urls    = [ZIP_URL]

elif TARGET == "macOS":
    # Use version‑pinned universal builds so ffprobe is guaranteed to exist.
    BASE = "https://evermeet.cx/ffmpeg"
    VERSION = "120072-g11d1b71c31"
    urls  = [f"{BASE}/ffmpeg-{VERSION}.zip", f"{BASE}/ffprobe-{VERSION}.zip"]
    NAMES = ["ffmpeg", "ffprobe"]

elif TARGET == "Linux":
    # CI installs distro ffmpeg; copy it instead of downloading.
    for tool in ["ffmpeg", "ffprobe"]:
        src = shutil.which(tool)
        if not src:
            sys.exit(f"{tool} not found on Linux runner")
        shutil.copy(src, DEST / tool)
        os.chmod(DEST / tool, 0o755)
    print(f"Copied system ffmpeg & ffprobe → {DEST}")
    sys.exit(0)

else:
    sys.exit(f"Unknown target '{TARGET}'")

print(f"Fetching static {NAMES} for {TARGET} ...")

for url in urls:
    tmp_fd, tmp_path = tempfile.mkstemp()
    os.close(tmp_fd)
    urllib.request.urlretrieve(url, tmp_path)

    if zipfile.is_zipfile(tmp_path):
        with zipfile.ZipFile(tmp_path) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                if want(info.filename, NAMES):
                    with z.open(info) as src:
                        save(src, pathlib.Path(info.filename).name)
    else:                                  # tarball (Windows never hits this)
        with tarfile.open(tmp_path) as t:
            for member in t.getmembers():
                if member.isfile() and want(member.name, NAMES):
                    with t.extractfile(member) as src:
                        save(src, pathlib.Path(member.name).name)

    os.remove(tmp_path)

print(f"ffmpeg & ffprobe saved to {DEST}")
