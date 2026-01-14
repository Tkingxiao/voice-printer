# core/temp_manager.py
import tempfile
import shutil


class TempDir:
    def __init__(self, prefix="audio_concat_"):
        self.path = tempfile.mkdtemp(prefix=prefix)

    def file(self, name):
        return f"{self.path}/{name}"

    def cleanup(self):
        try:
            shutil.rmtree(self.path)
        except:
            pass
