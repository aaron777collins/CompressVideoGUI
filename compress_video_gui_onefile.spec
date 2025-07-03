# compress_video_gui_onefile.spec
import platform
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules
block_cipher = None

# --- decide which static ffmpeg build to add --------------------------------
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

# --- analysis ---------------------------------------------------------------
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
    console=False,         # GUI only
    icon=None,
)

# -- ONE‑FILE bundle ---------------------------------------------------------
app = PKG(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="CompressVideo",
)
