# core/audio_concat.py
import os
from .ffmpeg_utils import get_ffmpeg_path, run_ffmpeg
from .temp_manager import TempDir


class AudioConcatenator:
    def __init__(self):
        self.ffmpeg = get_ffmpeg_path()

    def concat(self, audio_files: list, output_file: str):
        temp = TempDir()

        try:
            list_file = temp.file("files.txt")
            with open(list_file, "w", encoding="utf-8") as f:
                for p in audio_files:
                    p = p.replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{p}'\n")

            cmd = [
                self.ffmpeg,
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_file,
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                "-y",
                output_file,
            ]

            run_ffmpeg(cmd)

        finally:
            temp.cleanup()
