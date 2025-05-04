import sounddevice as sd
import numpy as np
import pystray
import threading
import sys
import os
from PIL import Image, ImageDraw, ImageFont

class VirtualMic:
    def __init__(self):
        self.running = True
        
    def audio_loop(self):
        """音频转发主逻辑"""
        def callback(indata, outdata, frames, time, status):
            outdata[:] = indata  # 直接转发音频数据
            
        with sd.Stream(
            device=(sd.default.device[0], self.find_vb_cable()),
            channels=1,
            callback=callback,
            samplerate=44100
        ):
            while self.running:
                sd.sleep(1000)
    
    def find_vb_cable(self):
        """查找VB-CABLE设备索引"""
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if "CABLE Input" in device["name"] and device["max_input_channels"] > 0:
                return i
        return None
    
    def create_emoji_icon(self):
        """生成🎤表情托盘图标"""
        # 创建透明背景图像
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        try:
            # Windows系统Emoji字体路径
            font_path = "C:/Windows/Fonts/seguiemj.ttf"  
            font = ImageFont.truetype(font_path, 50)
        except:
            # 备用方案：使用默认字体（可能显示为方框）
            try:
                font = ImageFont.truetype("arial.ttf", 50)
            except:
                font = ImageFont.load_default()
        
        # 绘制🎤表情（居中）
        draw.text((12, 5), "🎤", font=font, fill="white")
        return image
    
    def create_tray(self):
        """创建系统托盘图标"""
        menu = pystray.Menu(
            pystray.MenuItem("退出", self.stop)
        )
        self.icon = pystray.Icon(
            "virtual_mic",
            icon=self.create_emoji_icon(),
            title="虚拟麦克风",
            menu=menu
        )
        self.icon.run()
    
    def stop(self):
        """安全退出程序"""
        self.running = False
        self.icon.stop()
        sys.exit(0)

if __name__ == "__main__":
    # Windows隐藏控制台窗口
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    # 启动程序
    vm = VirtualMic()
    threading.Thread(target=vm.audio_loop, daemon=True).start()  # 音频线程
    vm.create_tray()  # 托盘主线程
