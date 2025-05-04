# virtual-mic
（readme待修改）这是一个个人需要的虚拟麦克风软件。未曾尝试，谨慎使用！
# 🎤 虚拟麦克风转发工具

**无需安装驱动！** 通过 Python 将物理麦克风声音转发到虚拟设备。

## 使用方法
# 方法1
1. 克隆本仓库：
   ```bash
   git clone https://github.com/HMwancheng/virtual-mic.git
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
3. 运行：
   ```bash
   python virtual_mic.py
4. 在录音软件中选择 立体声混音 作为麦克风输入。
⚠️ 需提前在系统声音设置中启用 立体声混音（Windows）或 Monitor of Sound（Linux）

## Linux/macOS适配
**在create_emoji_icon()中添加：**
   ```python
elif sys.platform == 'darwin':  # macOS
    font_path = "/System/Library/Fonts/Apple Color Emoji.ttf"
elif sys.platform == 'linux':
    font_path = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
