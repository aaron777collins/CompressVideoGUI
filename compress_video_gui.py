#!/usr/bin/env python3
"""
compress_video_gui.py
A tiny ffmpeg front‑end for one‑click H.265 compression.
"""

import os
import re
import shlex
import subprocess
import shutil, platform, sys
from pathlib import Path
from datetime import timedelta

from PyQt5 import QtCore, QtGui, QtWidgets


def find_tool(name: str) -> str:
    """
    Return an absolute path to 'ffmpeg' or 'ffprobe'.

    • When the app is frozen (PyInstaller) we first look inside the
      temporary extraction dir (sys._MEIPASS) where we will bundle
      the binaries.
    • Otherwise we fall back to the user's PATH.
    """
    if getattr(sys, 'frozen', False):
        cand = Path(sys._MEIPASS) / (name + (".exe" if platform.system() == "Windows" else ""))
        if cand.is_file():
            return str(cand)
    return shutil.which(name) or name


FFMPEG  = find_tool("ffmpeg")
FFPROBE = find_tool("ffprobe")


# ---------- helper functions -------------------------------------------------
def seconds_from_timestamp(ts: str) -> float:
    """Convert ffmpeg h:m:s.xx timestamp to seconds."""
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def probe_duration(path: Path) -> float | None:
    """Return media duration in seconds using ffprobe, or None on failure."""
    cmd = [FFPROBE, "-v", "error", "-select_streams", "v:0",
           "-show_entries", "format=duration", "-of",
           "default=noprint_wrappers=1:nokey=1", str(path)]
    creationflags = 0
    if platform.system() == "Windows":
        creationflags = subprocess.CREATE_NO_WINDOW
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, creationflags=creationflags).strip()
        return float(out)
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None


# ---------- worker thread ----------------------------------------------------
class EncodeWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)       # 0‑100
    finished = QtCore.pyqtSignal(bool, str) # success flag, message

    def __init__(self, infile: str, outfile: str, crf: int, parent=None):
        super().__init__(parent)
        self.infile = infile
        self.outfile = outfile
        self.crf = crf
        self._re_time = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")
        self._cancelled = False

    def run(self) -> None:
        total = probe_duration(Path(self.infile))
        creationflags = 0
        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NO_WINDOW
        cmd = [FFMPEG, "-y", "-i", self.infile,
               "-vcodec", "libx265", "-crf", str(self.crf),
               self.outfile]
        try:
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    universal_newlines=True,
                                    creationflags=creationflags)
        except FileNotFoundError:
            self.finished.emit(False, "ffmpeg executable not found.")
            return

        # Monitor stderr for timestamps
        for line in proc.stderr:
            if self._cancelled:
                proc.kill()
                proc.wait()
                self.finished.emit(False, "Encoding cancelled.")
                return
            m = self._re_time.search(line)
            if m and total:
                elapsed = seconds_from_timestamp(m.group(1))
                pct = max(0, min(100, int((elapsed / total) * 100)))
                self.progress.emit(pct)

        proc.wait()
        if proc.returncode == 0:
            self.progress.emit(100)
            self.finished.emit(True, "Compression completed ✓")
        else:
            self.finished.emit(False, f"ffmpeg exited with code {proc.returncode}")

    def cancel(self):
        self._cancelled = True


# ---------- main window ------------------------------------------------------
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("H.265 Video Compressor")
        self.setFixedSize(500, 230)
        self.setWindowIcon(QtGui.QIcon.fromTheme("video-x-generic"))

        # Widgets -------------------------------------------------------------
        self.in_edit  = QtWidgets.QLineEdit()
        self.out_edit = QtWidgets.QLineEdit()
        self.browse_in_btn  = QtWidgets.QPushButton("Browse…")
        self.browse_out_btn = QtWidgets.QPushButton("Browse…")

        self.crf_box = QtWidgets.QSpinBox()
        self.crf_box.setRange(0, 51)
        self.crf_box.setValue(28)
        self.crf_box.setToolTip("Lower CRF = higher quality & larger file.")

        self.start_btn  = QtWidgets.QPushButton("Start")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)

        self.progress_bar = QtWidgets.QProgressBar()
        self.status_label = QtWidgets.QLabel("Select an input file to begin.")

        # Layout --------------------------------------------------------------
        grid = QtWidgets.QGridLayout(self)
        grid.addWidget(QtWidgets.QLabel("Input MP4:"),  0, 0)
        grid.addWidget(self.in_edit,                    0, 1)
        grid.addWidget(self.browse_in_btn,              0, 2)

        grid.addWidget(QtWidgets.QLabel("Output MP4:"), 1, 0)
        grid.addWidget(self.out_edit,                   1, 1)
        grid.addWidget(self.browse_out_btn,             1, 2)

        grid.addWidget(QtWidgets.QLabel("CRF:"),        2, 0)
        grid.addWidget(self.crf_box,                    2, 1)

        btn_box = QtWidgets.QHBoxLayout()
        btn_box.addStretch()
        btn_box.addWidget(self.start_btn)
        btn_box.addWidget(self.cancel_btn)
        grid.addLayout(btn_box,                         3, 0, 1, 3)

        grid.addWidget(self.progress_bar,               4, 0, 1, 3)
        grid.addWidget(self.status_label,               5, 0, 1, 3)

        # Signals -------------------------------------------------------------
        self.browse_in_btn.clicked.connect(self.select_infile)
        self.browse_out_btn.clicked.connect(self.select_outfile)
        self.start_btn.clicked.connect(self.start_encode)
        self.cancel_btn.clicked.connect(self.cancel_encode)

        self.worker: EncodeWorker | None = None

    # --------- slots --------------------------------------------------------
    def select_infile(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select input video", "",
            "MP4 Video (*.mp4);;All files (*)")
        if path:
            self.in_edit.setText(path)
            # auto‑suggest output file in same folder
            if not self.out_edit.text():
                out_path = Path(path).with_stem(Path(path).stem + "_h265")
                self.out_edit.setText(str(out_path))

    def select_outfile(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save output video", "",
            "MP4 Video (*.mp4)")
        if path:
            if not path.lower().endswith(".mp4"):
                path += ".mp4"
            self.out_edit.setText(path)

    def start_encode(self):
        infile  = self.in_edit.text().strip('"')
        outfile = self.out_edit.text().strip('"')
        crf     = self.crf_box.value()

        if not infile or not outfile:
            QtWidgets.QMessageBox.warning(self, "Missing fields",
                                          "Please choose both input and output files.")
            return
        if not Path(infile).is_file():
            QtWidgets.QMessageBox.critical(self, "Input error",
                                           "Input file does not exist.")
            return
        if os.path.abspath(infile) == os.path.abspath(outfile):
            QtWidgets.QMessageBox.critical(self, "Path error",
                                           "Input and output cannot be the same file.")
            return

        self.progress_bar.setValue(0)
        self.status_label.setText("Starting ffmpeg…")
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        self.worker = EncodeWorker(infile, outfile, crf)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.encode_finished)
        self.worker.start()

    def cancel_encode(self):
        if self.worker:
            self.worker.cancel()
            self.status_label.setText("Cancelling…")

    def encode_finished(self, ok: bool, message: str):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText(message)
        if not ok:
            QtWidgets.QMessageBox.critical(self, "Error", message)
        else:
            QtWidgets.QMessageBox.information(self, "Done", message)


# ---------- entry‑point ------------------------------------------------------
def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")  # prettier default palette
    wnd = MainWindow()
    wnd.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
