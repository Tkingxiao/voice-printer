# core/audio_library.py
import os
import random


class AudioLibrary:
    """管理 字符 → 音频文件 映射"""

    def __init__(self, voice_dir, speaker):
        self.voice_dir = voice_dir
        self.speaker = speaker
        self.map = {}

    def load(self):
        self.map.clear()
        base = os.path.join(self.voice_dir, self.speaker)

        for char in os.listdir(base):
            char_dir = os.path.join(base, char)
            if not os.path.isdir(char_dir):
                continue

            mp3s = [f for f in os.listdir(char_dir) if f.lower().endswith(".mp3")]
            if mp3s:
                self.map[char] = mp3s

    def has_char(self, char):
        return char in self.map

    def random_audio(self, char):
        filename = random.choice(self.map[char])
        return os.path.abspath(
            os.path.join(self.voice_dir, self.speaker, char, filename)
        )
