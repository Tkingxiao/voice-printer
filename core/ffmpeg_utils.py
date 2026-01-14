# core/ffmpeg_utils.py
import os
import sys
import subprocess


def get_ffmpeg_path():
    """自动获取 ffmpeg 路径（开发 / PyInstaller）"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "ffmpeg.exe")
    return "ffmpeg"


def run_ffmpeg(cmd: list):
    """统一执行 ffmpeg，隐藏窗口"""
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

    subprocess.run(
        cmd,
        startupinfo=startupinfo,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
    )
