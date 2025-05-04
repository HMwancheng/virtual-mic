import sys
import os
import ctypes
import threading
from ctypes import wintypes
from PIL import Image, ImageDraw, ImageFont
import io

# ======================
# 初始化设置
# ======================
if sys.platform != "win32":
    raise RuntimeError("This application only supports Windows")

# ======================
# Emoji图标生成器
# ======================
def generate_emoji_icon():
    """生成🎤表情的托盘图标"""
    try:
        # 尝试加载系统Emoji字体
        if sys.platform == "win32":
            font_path = "C:/Windows/Fonts/seguiemj.ttf"
        elif sys.platform == "darwin":
            font_path = "/System/Library/Fonts/Apple Color Emoji.ttf"
        else:
            font_path = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
        
        font = ImageFont.truetype(font_path, 60)
    except:
        # 备用方案：使用默认字体
        font = ImageFont.load_default()
    
    # 创建透明背景图像
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制🎤表情（调整位置居中）
    draw.text((12, -5), "🎤", font=font, fill="white")
    
    # 转换为Windows需要的图标格式
    with io.BytesIO() as output:
        img.save(output, format='ICO', sizes=[(64, 64)])
        return output.getvalue()

# ======================
# Windows API 定义
# ======================
class NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uVersion", wintypes.UINT),
    ]

# ======================
# 音频处理核心
# ======================
def audio_loop(stop_event):
    """音频转发线程"""
    import sounddevice as sd
    
    def callback(indata, outdata, frames, time, status):
        outdata[:] = indata
    
    try:
        with sd.Stream(
            channels=1,
            callback=callback,
            samplerate=44100,
            blocksize=1024
        ):
            while not stop_event.is_set():
                sd.sleep(1000)
    except Exception as e:
        print(f"Audio error: {e}")

# ======================
# 托盘图标管理
# ======================
class TrayIcon:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.shell32 = ctypes.windll.shell32
        self.gdi32 = ctypes.windll.gdi32
        
        # 生成Emoji图标
        ico_data = generate_emoji_icon()
        self.setup_icon(ico_data)
        
        # 初始化NOTIFYICONDATA
        self.nid = NOTIFYICONDATA()
        self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
        self.nid.uFlags = 0x1 | 0x2  # NIF_ICON | NIF_MESSAGE
        self.nid.uCallbackMessage = 0x400 + 1
        self.nid.szTip = "Virtual Mic\0"
    
    def setup_icon(self, ico_data):
        """将内存中的ICO数据转换为HICON"""
        # 临时保存ICO文件
        temp_ico = os.path.join(os.environ['TEMP'], 'vm_temp.ico')
        with open(temp_ico, 'wb') as f:
            f.write(ico_data)
        
        # 加载图标
        self.nid.hIcon = self.user32.LoadImageW(
            0, temp_ico, 1, 0, 0, 0x10|0x20  # LR_LOADFROMFILE|LR_DEFAULTSIZE
        )
        
        # 删除临时文件
        try:
            os.remove(temp_ico)
        except:
            pass
    
    def show(self):
        """显示托盘图标"""
        self.shell32.Shell_NotifyIconW(0x0, ctypes.byref(self.nid))  # NIM_ADD
    
    def remove(self):
        """移除托盘图标"""
        if hasattr(self, 'nid'):
            self.shell32.Shell_NotifyIconW(0x2, ctypes.byref(self.nid))  # NIM_DELETE
            self.gdi32.DeleteObject(self.nid.hIcon)

# ======================
# 主程序
# ======================
def main():
    # 隐藏控制台窗口
    ctypes.windll.user32.ShowWindow(
        ctypes.windll.kernel32.GetConsoleWindow(), 0
    )
    
    # 创建停止事件
    stop_event = threading.Event()
    
    # 启动音频线程
    audio_thread = threading.Thread(
        target=audio_loop,
        args=(stop_event,),
        daemon=True
    )
    audio_thread.start()
    
    # 初始化托盘图标
    tray = TrayIcon()
    tray.show()
    
    try:
        # Windows消息循环
        msg = wintypes.MSG()
        while True:
            if tray.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) <= 0:
                break
                
            if msg.message == tray.nid.uCallbackMessage:
                if msg.lParam == 0x0205:  # WM_RBUTTONUP
                    tray.user32.PostQuitMessage(0)
            
            tray.user32.TranslateMessage(ctypes.byref(msg))
            tray.user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        stop_event.set()
        tray.remove()
        audio_thread.join(timeout=1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(
            0, f"程序错误: {str(e)}", "Virtual Mic", 0x10
        )
