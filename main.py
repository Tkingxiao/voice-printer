import os
import sys
import random
from pathlib import Path
import shutil
from pydub import AudioSegment
import subprocess
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QTextEdit,
    QLabel,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QGroupBox,
    QGridLayout,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from core.audio_library import AudioLibrary
from core.audio_concat import AudioConcatenator


class AudioProcessor(QThread):
    """后台音频处理线程"""

    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, voice_dir, speaker):
        super().__init__()
        self.voice_dir = voice_dir
        self.speaker = speaker
        self.speaker_path = os.path.join(voice_dir, speaker)

    def run(self):
        try:
            self.status_signal.emit("开始整理音频文件...")

            # ============ 修改部分：确定ffmpeg路径 ============
            # 优先使用打包的ffmpeg
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller打包后的临时目录
                ffmpeg_path = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
            else:
                # 开发环境，使用系统PATH中的ffmpeg
                ffmpeg_path = 'ffmpeg'

            # ============ 修改结束 ============

            # 获取所有单字文件夹
            char_folders = [
                f
                for f in os.listdir(self.speaker_path)
                if os.path.isdir(os.path.join(self.speaker_path, f))
            ]

            total_folders = len(char_folders)

            for idx, char_folder in enumerate(char_folders):
                folder_path = os.path.join(self.speaker_path, char_folder)

                # 获取文件夹中所有音频文件
                audio_files = []
                for ext in [
                    '*.mp3',
                    '*.wav',
                    '*.m4a',
                    '*.ogg',
                    '*.flac',
                    '*.aac',
                    '*.wma',
                ]:
                    audio_files.extend(Path(folder_path).glob(ext))

                # 转换非mp3文件为mp3（使用ffmpeg）
                for i, audio_file in enumerate(audio_files):
                    file_ext = audio_file.suffix.lower()

                    # 如果是mp3文件，跳过转换
                    if file_ext == '.mp3':
                        continue

                    try:
                        self.status_signal.emit(
                            f"转换文件: {char_folder}/{audio_file.name}"
                        )

                        # 生成临时输出文件名
                        temp_output = audio_file.with_suffix('.temp.mp3')
                        output_file = audio_file.with_suffix('.mp3')

                        # 构建ffmpeg转换命令
                        if file_ext in ['.wav', '.flac']:
                            # 无损格式，使用高质量转换
                            cmd = [
                                ffmpeg_path,
                                '-i',
                                str(audio_file),
                                '-codec:a',
                                'libmp3lame',
                                '-q:a',
                                '2',  # 高质量 (2-最高质量, 9-最低质量)
                                '-y',  # 覆盖输出
                                str(temp_output),
                            ]
                        elif file_ext in ['.m4a', '.aac']:
                            # AAC格式，保持较好质量
                            cmd = [
                                ffmpeg_path,
                                '-i',
                                str(audio_file),
                                '-codec:a',
                                'libmp3lame',
                                '-b:a',
                                '192k',  # 192kbps比特率
                                '-y',
                                str(temp_output),
                            ]
                        elif file_ext in ['.ogg']:
                            # OGG Vorbis格式
                            cmd = [
                                ffmpeg_path,
                                '-i',
                                str(audio_file),
                                '-codec:a',
                                'libmp3lame',
                                '-b:a',
                                '160k',
                                '-y',
                                str(temp_output),
                            ]
                        elif file_ext in ['.wma']:
                            # WMA格式
                            cmd = [
                                ffmpeg_path,
                                '-i',
                                str(audio_file),
                                '-codec:a',
                                'libmp3lame',
                                '-b:a',
                                '128k',
                                '-y',
                                str(temp_output),
                            ]
                        else:
                            # 其他格式，使用默认设置
                            cmd = [
                                ffmpeg_path,
                                '-i',
                                str(audio_file),
                                '-codec:a',
                                'libmp3lame',
                                '-b:a',
                                '128k',
                                '-y',
                                str(temp_output),
                            ]

                        # 执行ffmpeg转换
                        startupinfo = None
                        if sys.platform == 'win32':
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = subprocess.SW_HIDE

                        result = subprocess.run(
                            cmd,
                            startupinfo=startupinfo,
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='ignore',
                            timeout=30,  # 30秒超时
                        )

                        if result.returncode == 0:
                            # 转换成功，重命名为最终文件名
                            if temp_output.exists():
                                # 如果目标文件已存在，先删除
                                if output_file.exists():
                                    output_file.unlink()
                                temp_output.rename(output_file)

                                # 删除原文件
                                audio_file.unlink()
                                print(
                                    f"转换成功: {audio_file.name} -> {output_file.name}"
                                )
                            else:
                                print(f"转换失败: 输出文件不存在 {temp_output}")
                        else:
                            print(f"FFmpeg转换失败 {audio_file}: {result.stderr[:100]}")

                            # 尝试简单命令作为备选方案
                            try:
                                simple_cmd = [
                                    ffmpeg_path,
                                    '-i',
                                    str(audio_file),
                                    str(output_file),
                                ]
                                subprocess.run(
                                    simple_cmd,
                                    startupinfo=startupinfo,
                                    capture_output=True,
                                    timeout=30,
                                )
                                if output_file.exists():
                                    audio_file.unlink()
                                    print(f"简单转换成功: {audio_file.name}")
                            except Exception as e2:
                                print(f"备选方案也失败: {e2}")

                    except subprocess.TimeoutExpired:
                        print(f"转换超时: {audio_file.name}")
                    except Exception as e:
                        print(f"转换失败 {audio_file}: {e}")

                # 重新获取mp3文件
                mp3_files = list(Path(folder_path).glob('*.mp3'))

                # 重命名并重新编号
                for i, mp3_file in enumerate(mp3_files, 1):
                    new_name = f"{char_folder}_{i}.mp3"
                    new_path = os.path.join(folder_path, new_name)

                    # 如果文件名已经正确，跳过
                    if mp3_file.name == new_name:
                        continue

                    # 处理重名文件
                    counter = 1
                    while os.path.exists(new_path):
                        new_name = f"{char_folder}_{i}_{counter}.mp3"
                        new_path = os.path.join(folder_path, new_name)
                        counter += 1

                    try:
                        shutil.move(str(mp3_file), new_path)
                    except Exception as e:
                        print(f"重命名失败 {mp3_file}: {e}")

                # 更新进度
                progress = int((idx + 1) / total_folders * 100)
                self.progress_signal.emit(progress)

            self.status_signal.emit("音频整理完成！")
            self.finished_signal.emit(True)

        except Exception as e:
            self.status_signal.emit(f"处理出错: {str(e)}")
            self.finished_signal.emit(False)


class ConcatWorker(QThread):
    status = pyqtSignal(str)  # 实时状态
    error = pyqtSignal(str)  # 错误信息
    done = pyqtSignal(str)  # 返回最终 mp3 路径

    def __init__(self, ffmpeg_path, list_file, out_file):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self.list_file = list_file
        self.out_file = out_file

    def run(self):
        try:
            self.status.emit("正在拼接音频……")
            cmd = [
                self.ffmpeg_path,
                '-f',
                'concat',
                '-safe',
                '0',
                '-i',
                self.list_file,
                '-c:a',
                'libmp3lame',
                '-b:a',
                '192k',
                '-y',
                self.out_file,
            ]

            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            subprocess.run(
                cmd,
                startupinfo=startupinfo,
                check=True,
                capture_output=True,
                encoding='utf-8',
            )
            self.done.emit(self.out_file)
        except subprocess.CalledProcessError as e:
            self.error.emit("FFmpeg 拼接失败：\n" + e.stderr)
        except Exception as e:
            self.error.emit(str(e))


class LiveTypePrinter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.voice_dir = "voice"  # 默认音频文件夹
        self.current_speaker = None
        self.char_audio_map = {}  # 存储字符对应的音频文件列表
        self.init_ui()
        self.load_speakers()

    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("活字印刷机")
        self.setGeometry(100, 100, 850, 700)

        # 设置应用样式
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2196F3;
            }
            QPushButton {
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QLabel {
                padding: 2px;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """
        )

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 标题
        title_label = QLabel("活字印刷机")
        title_font = QFont("微软雅黑", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(
            """
            QLabel {
                color: #2196F3;
                padding: 15px;
                background-color: white;
                border-radius: 8px;
                border: 2px solid #2196F3;
            }
        """
        )
        main_layout.addWidget(title_label)

        # ==================== 控制面板区域 ====================
        control_group = QGroupBox("控制面板")
        control_layout = QGridLayout()
        control_layout.setSpacing(15)
        control_layout.setContentsMargins(15, 20, 15, 15)

        # 音频目录选择
        self.dir_label = QLabel(f"音频目录: {self.voice_dir}")
        self.dir_label.setStyleSheet(
            "color: #333333; font-weight: bold; font-size: 15px;"
        )
        self.dir_button = QPushButton("更改目录")
        self.dir_button.setStyleSheet("background-color: #2196F3; font-size: 14px;")
        self.dir_button.clicked.connect(self.change_voice_dir)

        # 主播选择
        speaker_label = QLabel("选择主播:")
        speaker_label.setStyleSheet(
            "color: #333333; font-weight: bold; font-size: 15px;"
        )

        self.speaker_combo = QComboBox()
        self.speaker_combo.setMinimumHeight(30)
        self.speaker_combo.setStyleSheet(
            """
            QComboBox {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
            color: #333333;  /* 正常状态文字颜色 */
            font-size: 14px;
            selection-background-color: #2196F3;  /* 选中项背景色 */
            selection-color: white;  /* 选中项文字颜色 */
            }
            QComboBox QAbstractItemView {
            font-size: 14px;  /* 下拉列表项的字体大小 */
            }
            QComboBox:hover {
            border: 1px solid #2196F3;
            background-color: white;
            color: #333333;  /* 悬停时文字颜色 */
            }
        """
        )
        self.speaker_combo.currentTextChanged.connect(self.change_speaker)

        refresh_button = QPushButton("刷新列表")
        refresh_button.setStyleSheet("background-color: #607D8B; font-size: 14px;")
        refresh_button.clicked.connect(self.load_speakers)

        # 整理音频按钮
        self.organize_button = QPushButton("整理当前主播音频")
        self.organize_button.setStyleSheet(
            "background-color: #FF9800; font-size: 14px;"
        )
        self.organize_button.clicked.connect(self.organize_audio)
        self.organize_button.setEnabled(False)

        # 添加到控制布局
        control_layout.addWidget(speaker_label, 0, 0)
        control_layout.addWidget(self.speaker_combo, 0, 1, 1, 2)
        control_layout.addWidget(refresh_button, 0, 3)
        control_layout.addWidget(self.dir_label, 1, 0, 1, 2)
        control_layout.addWidget(self.dir_button, 1, 2, 1, 2)
        control_layout.addWidget(self.organize_button, 2, 0, 1, 4)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # ==================== 进度和状态区域 ====================
        progress_group = QGroupBox("处理状态")
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(10)
        progress_layout.setContentsMargins(15, 20, 15, 15)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(40)
        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #666666;
                font-weight: bold;
                font-size: 14px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """
        )

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # ==================== 输入区域 ====================
        input_group = QGroupBox("文字输入")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(10)
        input_layout.setContentsMargins(15, 20, 15, 15)

        self.text_input = QTextEdit()
        self.text_input.setStyleSheet(
            """
            QTextEdit {
                font-size: 14px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 10px;
                background-color: white;
            }
        """
        )
        self.text_input.setPlaceholderText("请输入要转换的文字...")
        self.text_input.setMinimumHeight(120)

        input_buttons_layout = QHBoxLayout()
        input_buttons_layout.setSpacing(10)

        self.generate_button = QPushButton("生成语音")
        self.generate_button.setStyleSheet("background-color: #4CAF50;")
        self.generate_button.clicked.connect(self.generate_audio)
        self.generate_button.setEnabled(False)

        self.clear_button = QPushButton("清空文本")
        self.clear_button.setStyleSheet("background-color: #9E9E9E;")
        self.clear_button.clicked.connect(self.clear_text)

        input_buttons_layout.addWidget(self.generate_button)
        input_buttons_layout.addWidget(self.clear_button)
        input_buttons_layout.addStretch()

        input_layout.addWidget(self.text_input)
        input_layout.addLayout(input_buttons_layout)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # ==================== 信息显示区域 ====================
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(15, 20, 15, 15)

        self.info_label = QLabel("当前主播: 未选择\n可用字符: 0")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setMinimumHeight(80)
        self.info_label.setStyleSheet(
            """
            QLabel {
                background-color: #e8f4fd;
                padding: 15px;
                border-radius: 8px;
                border: 2px solid #bbdefb;
                color: #0d47a1;
                font-weight: bold;
                font-size: 14px;
            }
        """
        )

        info_layout.addWidget(self.info_label)
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        main_layout.addStretch()

    def change_voice_dir(self):
        """更改音频目录"""
        new_dir = QFileDialog.getExistingDirectory(self, "选择音频目录", ".")
        if new_dir:
            self.voice_dir = new_dir
            self.dir_label.setText(f"音频目录: {self.voice_dir}")
            self.load_speakers()

    def load_speakers(self):
        """加载主播列表"""
        self.speaker_combo.clear()

        if not os.path.exists(self.voice_dir):
            QMessageBox.warning(
                self, "目录不存在", f"音频目录 '{self.voice_dir}' 不存在！"
            )
            return

        speakers = [
            d
            for d in os.listdir(self.voice_dir)
            if os.path.isdir(os.path.join(self.voice_dir, d))
        ]

        if speakers:
            self.speaker_combo.addItems(speakers)
        else:
            self.speaker_combo.addItem("未找到主播")

    def change_speaker(self, speaker):
        """切换主播"""
        if speaker and speaker != "未找到主播":
            self.current_speaker = speaker
            self.organize_button.setEnabled(True)
            self.generate_button.setEnabled(True)
            self.load_char_audio()
        else:
            self.current_speaker = None
            self.organize_button.setEnabled(False)
            self.generate_button.setEnabled(False)
            self.char_audio_map = {}
            self.update_info_label()

    def load_char_audio(self):
        """加载主播的字符音频信息"""
        if not self.current_speaker:
            return

        speaker_path = os.path.join(self.voice_dir, self.current_speaker)
        self.char_audio_map = {}

        # 获取所有单字文件夹
        char_folders = [
            f
            for f in os.listdir(speaker_path)
            if os.path.isdir(os.path.join(speaker_path, f))
        ]

        for char in char_folders:
            char_path = os.path.join(speaker_path, char)
            # 获取该字符的所有音频文件
            audio_files = [
                f for f in os.listdir(char_path) if f.lower().endswith('.mp3')
            ]
            if audio_files:
                self.char_audio_map[char] = audio_files

        self.update_info_label()

    def update_info_label(self):
        """更新信息标签"""
        if self.current_speaker:
            available_chars = len(self.char_audio_map)
            info_text = (
                f"当前主播: {self.current_speaker}\n" f"可用字符: {available_chars}\n"
            )
        else:
            info_text = "当前主播: 未选择\n可用字符: 0\n请先选择主播并设置音频目录"
        self.info_label.setText(info_text)

    def organize_audio(self):
        """整理音频文件"""
        if not self.current_speaker:
            QMessageBox.warning(self, "错误", "请先选择主播！")
            return

        # 禁用按钮，显示进度条
        self.organize_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在整理音频文件...")

        # 创建并启动处理线程
        self.processor = AudioProcessor(self.voice_dir, self.current_speaker)
        self.processor.progress_signal.connect(self.progress_bar.setValue)
        self.processor.status_signal.connect(self.status_label.setText)
        self.processor.finished_signal.connect(self.on_organization_finished)
        self.processor.start()

    def on_organization_finished(self, success):
        """整理完成后的处理"""
        self.organize_button.setEnabled(True)
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            QMessageBox.information(self, "完成", "音频整理完成！")
            self.load_char_audio()  # 重新加载音频信息
            self.status_label.setText("音频整理完成")
        else:
            QMessageBox.warning(self, "错误", "音频整理过程中出现错误！")
            self.status_label.setText("整理失败")

    def make_unique_path(self, path):

        if not os.path.exists(path):
            return path

        base, ext = os.path.splitext(path)
        counter = 2
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def generate_audio(self):
        if not self.current_speaker:
            QMessageBox.warning(self, "错误", "请先选择主播！")
            return

        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "错误", "请输入要转换的文字！")
            return

        lib = AudioLibrary(self.voice_dir, self.current_speaker)
        lib.load()

        missing = [c for c in text if c.strip() and not lib.has_char(c)]
        if missing:
            if (
                QMessageBox.question(
                    self,
                    "缺少字符",
                    f"以下字符没有音频：{', '.join(set(missing))}\n是否继续？",
                    QMessageBox.Yes | QMessageBox.No,
                )
                == QMessageBox.No
            ):
                return

        audio_files = [
            lib.random_audio(c) for c in text if c.strip() and lib.has_char(c)
        ]

        if not audio_files:
            QMessageBox.warning(self, "错误", "没有可用音频")
            return

        os.makedirs("输出目录", exist_ok=True)
        base_outfile = os.path.join(
            "输出目录", f"{self.current_speaker}_{text[:20]}.mp3"
        )
        outfile = self.make_unique_path(base_outfile)

        self.status_label.setText("正在生成音频...")
        QApplication.processEvents()

        try:
            AudioConcatenator().concat(audio_files, outfile)
            self.status_label.setText(f"生成完成：{os.path.basename(outfile)}")
        except Exception as e:
            QMessageBox.critical(self, "失败", str(e))
            self.status_label.setText("生成失败")

    def clear_text(self):
        """清空输入文本"""
        self.text_input.clear()

    # -------------- 槽：进度/错误/完成 --------------
    def _concat_status(self, msg):
        self.status_label.setText(msg)

    def _concat_error(self, msg):
        QMessageBox.critical(self, "拼接失败", msg)
        self.status_label.setText("生成失败")

    def _concat_done(self, outfile):
        """拼接完成：清理临时文件 + 询问播放"""
        try:
            os.remove(self._temp_list_file)
            os.rmdir(self._temp_dir)
        except:
            pass
        self.status_label.setText(f"音频生成完成：{os.path.basename(outfile)}")
        if (
            QMessageBox.question(
                self,
                "完成",
                f"已保存到：{outfile}\n是否立即播放？",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            self.play_audio(outfile)


def main():
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle('Fusion')

    # 自定义消息框样式
    app.setStyleSheet(
        """
        QMessageBox {
            background-color: white;
        }
        QMessageBox QLabel {
            color: #333333;
        }
        QMessageBox QPushButton {
            background-color: #2196F3;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #1976D2;
        }
        QMessageBox QPushButton[text="No"],
        QMessageBox QPushButton[text="否"] {
            background-color: #f44336;
        }
        QMessageBox QPushButton[text="No"]:hover,
        QMessageBox QPushButton[text="否"]:hover {
            background-color: #da190b;
        }
    """
    )

    window = LiveTypePrinter()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
