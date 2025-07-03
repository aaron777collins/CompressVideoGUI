# compress_video_gui.spec
# PyInstaller build recipe for “CompressVideo”

# ---- imports ----
from PyInstaller.utils.hooks import collect_submodules
block_cipher = None

# ---- analysis ----
a = Analysis(
    ["compress_video_gui.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules("PyQt5"),
    hookspath=[],
    runtime_hooks=[],
    cipher=block_cipher,
)

# ---- build ----
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CompressVideo",
    console=False,          # no terminal window on Windows/macOS
    icon=None,              # add a .ico/.icns path here if you have one
)

# ---- bundle ----
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
