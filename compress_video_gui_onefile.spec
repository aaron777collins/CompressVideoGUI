# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
import platform
from pathlib import Path
block_cipher = None

# -------- bundle our pre‑fetched ffmpeg binaries ---------------------------
bins = []
plat = platform.system()
if plat == "Windows":
    bins += [(str(Path("externals/windows/ffmpeg.exe")),  "."),
             (str(Path("externals/windows/ffprobe.exe")), ".")]
elif plat == "Darwin":
    bins += [(str(Path("externals/macos/ffmpeg")),  "."),
             (str(Path("externals/macos/ffprobe")), ".")]
else:  # Linux
    bins += [(str(Path("externals/linux/ffmpeg")),  "."),
             (str(Path("externals/linux/ffprobe")), ".")]

# -------- normal build chain ----------------------------------------------
a = Analysis(
    ["compress_video_gui.py"],
    pathex=[],
    binaries=bins,
    datas=[],
    hiddenimports=collect_submodules("PyQt5"),
    hookspath=[],
    runtime_hooks=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CompressVideo",
    console=False,
    icon=None,
    onefile=True,        # <- produces *single* self‑extracting file
)

# NOTE: keep COLLECT; PyInstaller still generates it for one‑file specs.
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CompressVideo",
)
