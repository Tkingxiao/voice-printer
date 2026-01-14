# 活字印刷机 —— 把「文字」秒变「真人语音」的桌面小工具
## 🎧 一句话介绍
给主播「切」一堆**单字音频**，输入任意句子，程序自动**随机抽取**对应字的音频并**无缝拼接**成完整语音，像古代活字印刷一样“拼”出整段话！

---

## ✨ 特色
- **纯离线**：本地拼接，无需联网  
- **多主播**：支持多角色声音库，一键切换  
- **全格式**：自动把 `.wav / .flac / .m4a / .ogg …` 转成统一 `.mp3`  
- **防重复**：同字多音，每次随机挑选，避免机械感  
- **可视化**：PyQt5 图形界面，进度条实时显示  
- **单文件**：可打包成 **独立 exe**，拷给谁都直接跑  

---

## 📦 目录结构
```
活字印刷机/
├─ main.py                 # 主程序（GUI）
├─ core/                   # 核心模块
│  ├─ audio_library.py     # 字音库管理
│  ├─ audio_concat.py      # 音频拼接（ffmpeg）
│  ├─ ffmpeg_utils.py      # ffmpeg 统一调用
│  └─ temp_manager.py      # 临时文件清理
├─ voice/                  # 声音根目录
│  └─ 主播名字/            # 每主播一个文件夹
│     ├─ 你/               # 单字文件夹
│     ├─ 好/
│     └─ …
├─ 输出目录/               # 生成的 mp3 自动存这里
├─ ffmpeg.exe              # Windows 可放同目录（免配置）
└─ README.md               # 本文件
```

---

## 🚀 5 分钟上手

### ① 准备环境
```bash
# Python ≥3.8
pip install -r requirements.txt
```
> requirements.txt 只有两行：  
> `PyQt5>=5.15`  
> `pydub>=0.25`

### ② 准备音频
1. 在 `voice/` 下新建任意**主播文件夹**（如 `xiaoli`）  
2. 继续建**单字文件夹**，名字=汉字：  
   ```
   voice/xiaoli/你/你_1.mp3
   voice/xiaoli/你/你_2.wav   # 程序会自动转码
   voice/xiaoli/好/好_1.mp3
   ...
   ```
3. 把 [ffmpeg 可执行文件](https://ffmpeg.org/download.html) 扔进项目根目录（或确保已在系统 PATH）

### ③ 运行
```bash
python main.py
```
- 选择主播 → 整理音频（自动转码+重命名）→ 输入文字 → 生成语音  
- 结果保存在 `输出目录/主播名_文字前20字.mp3`

---

## 📦 打包成独立 exe（可选）

### Windows
```bash
pip install nuitka
python -m nuitka --standalone --onefile --windows-console-mode=disable \
       --include-data-file=ffmpeg.exe=ffmpeg.exe \
       --enable-plugin=pyqt5 --output-dir=dist main.py
```
生成的 `dist/main.exe` 双击即可运行，**无需 Python 环境**。

---

## ⚙️ 高级用法
| 场景 | 做法 |
|---|---|
| 新增主播 | 在 `voice/` 新建文件夹，重启程序即可识别 |
| 同字多音 | 同一字文件夹里放多条音频（`你_1.mp3 你_2.mp3 …`），程序随机挑 |
| 自定义码率 | 修改 `core/audio_concat.py` 中的 `-b:a 192k` |
| 命令行批量 | 直接 `import core` 模块，自己写脚本调用 `AudioLibrary` + `AudioConcatenator` |

---

## 🧩 核心 API（供二次开发）
```python
from core.audio_library import AudioLibrary
from core.audio_concat import AudioConcatenator

lib = AudioLibrary("voice", "xiaoli")
lib.load()                          # 加载字库
files = [lib.random_audio(c) for c in "你好世界"]
AudioConcatenator().concat(files, "output.mp3")
```

---

## 🐛 常见问题
| 现象 | 解决 |
|---|---|
| 生成失败，提示找不到 ffmpeg | 把 ffmpeg.exe 放项目根目录或加入系统 PATH |
| 缺少某字音频 | 程序会弹窗提示，可选择继续（跳过缺字）或取消 |
| 打包后 exe 很大 | 用 `--onefile` 会压成单文件；如仍大，可 UPX 加壳 |
| macOS / Linux 想运行 | 系统包管理器装 `ffmpeg`，其余同理 |

---

## 📄 许可证
MIT License —— 随便使用保留作者署名即可。

---

## ❤️ 作者
如有问题/建议，欢迎提 Issue 或 PR，让“活字印刷机”更好玩！