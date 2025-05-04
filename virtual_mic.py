import sys
import os
import ctypes
import threading
from ctypes import wintypes

# --- MinGW 兼容性补丁 ---
if sys.platform == "win32":
    # 解决MinGW环境下ctypes类型缺失问题
    if not hasattr(wintypes, 'LPDWORD'):
        wintypes.LPDWORD = ctypes.POINTER(wintypes.DWORD)
    
    # 打包后PATH处理
    if hasattr(sys, '_MEIPASS'):
        os.environ['PATH'] = sys._MEIPASS + ';' + os.environ['PATH']

# --- Windows API 定义 ---
class NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 64),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeout", wintypes.UINT),
    ]

# --- 音频处理核心 ---
def audio_loop():
    """极简音频转发实现"""
    import sounddevice as sd  # 延迟导入避免编译问题
    
    def callback(indata, outdata, frames, time, status):
        outdata[:] = indata  # 原生Python实现，避免numpy依赖
    
    with sd.Stream(
        channels=1,
        callback=callback,
        samplerate=44100,
        blocksize=1024
    ):
        while getattr(sys, 'running', True):
            sd.sleep(1000)

# --- 托盘图标管理 ---
class TrayManager:
    def __init__(self):
        self.shell32 = ctypes.windll.shell32
        self.user32 = ctypes.windll.user32
        
        # 初始化NOTIFYICONDATA结构
        self.nid = NOTIFYICONDATA()
        self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
        self.nid.uFlags = 0x1 | 0x2  # NIF_ICON | NIF_MESSAGE
        self.nid.szTip = "Virtual Mic\0"
        
        # 加载图标
        if os.path.exists("mic.ico"):
            self.nid.hIcon = self.user32.LoadImageW(
                0, "mic.ico", 1, 0, 0, 0x10
            )
    
    def show(self):
        """显示托盘图标"""
        self.shell32.Shell_NotifyIconW(0x0, ctypes.byref(self.nid))  # NIM_ADD
    
    def remove(self):
        """移除托盘图标"""
        self.shell32.Shell_NotifyIconW(0x2, ctypes.byref(self.nid))  # NIM_DELETE

# --- 主程序 ---
def main():
    # 隐藏控制台窗口
    if sys.platform == "win32":
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )
    
    # 启动音频线程
    sys.running = True
    audio_thread = threading.Thread(target=audio_loop, daemon=True)
    audio_thread.start()
    
    # 显示托盘图标
    if sys.platform == "win32":
        tray = TrayManager()
        tray.show()
        
        try:
            # 消息循环
            msg = wintypes.MSG()
            while sys.running and self.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            tray.remove()
    else:
        import time
        while sys.running:
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.running = False
