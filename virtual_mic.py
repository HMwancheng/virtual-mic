import sys
import os
import ctypes
import threading
from ctypes import wintypes

# ======================
# MinGW 兼容性补丁
# ======================
if sys.platform == "win32":
    # 补全MinGW可能缺少的类型定义
    if not hasattr(wintypes, 'LPDWORD'):
        wintypes.LPDWORD = ctypes.POINTER(wintypes.DWORD)
    
    # 处理打包后的资源路径
    if hasattr(sys, '_MEIPASS'):
        os.environ['PATH'] = sys._MEIPASS + ';' + os.environ['PATH']
        BASE_DIR = sys._MEIPASS
    else:
        BASE_DIR = os.path.dirname(__file__)
else:
    raise RuntimeError("This application only supports Windows")

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
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", wintypes.GUID),
        ("hBalloonIcon", wintypes.HICON),
    ]

# ======================
# 音频处理核心
# ======================
def audio_loop(stop_event):
    """音频转发线程"""
    import sounddevice as sd  # 延迟导入避免编译问题
    
    def callback(indata, outdata, frames, time, status):
        outdata[:] = indata  # 原生Python实现音频转发
    
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
        self.shell32 = ctypes.windll.shell32
        self.user32 = ctypes.windll.user32
        self.nid = NOTIFYICONDATA()
        self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
        self.nid.uFlags = 0x1 | 0x2 | 0x4  # NIF_ICON|NIF_MESSAGE|NIF_TIP
        self.nid.uCallbackMessage = 0x400 + 1
        
        # 加载图标
        icon_path = os.path.join(BASE_DIR, "mic.ico")
        if os.path.exists(icon_path):
            self.nid.hIcon = self.user32.LoadImageW(
                0, icon_path, 1, 0, 0, 0x10|0x20  # LR_LOADFROMFILE|LR_DEFAULTSIZE
            )
        
        self.nid.szTip = "Virtual Mic\0"
    
    def show(self):
        """显示托盘图标"""
        self.shell32.Shell_NotifyIconW(0x0, ctypes.byref(self.nid))  # NIM_ADD
    
    def remove(self):
        """移除托盘图标"""
        if hasattr(self, 'nid'):
            self.shell32.Shell_NotifyIconW(0x2, ctypes.byref(self.nid))  # NIM_DELETE

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
            if self.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) <= 0:
                break
                
            if msg.message == tray.nid.uCallbackMessage:
                # 处理托盘事件
                if msg.lParam == 0x0205:  # WM_RBUTTONUP
                    self.user32.PostQuitMessage(0)
            
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        stop_event.set()
        tray.remove()
        audio_thread.join(timeout=1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)
        ctypes.windll.user32.MessageBoxW(
            0, 
            f"程序崩溃: {str(e)}\n详见error.log", 
            "错误", 
            0x10
        )
