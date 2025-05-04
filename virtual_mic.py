import sys
import os
import ctypes
import threading
from ctypes import wintypes

# 极简版实现，移除所有非必要依赖
if sys.platform != "win32":
    raise SystemExit("Error: This app only works on Windows")

class VirtualMic:
    def __init__(self):
        self._setup_api()
        self.running = True

    def _setup_api(self):
        """初始化Windows API"""
        self.user32 = ctypes.WinDLL('user32')
        self.shell32 = ctypes.WinDLL('shell32')
        
        class NOTIFYICONDATA(ctypes.Structure):
            _fields_ = [
                ('cbSize', wintypes.DWORD),
                ('hWnd', wintypes.HWND),
                ('uID', wintypes.UINT),
                ('uFlags', wintypes.UINT),
                ('uCallbackMessage', wintypes.UINT),
                ('hIcon', wintypes.HICON),
                ('szTip', wintypes.WCHAR * 64)
            ]
        
        self.NOTIFYICONDATA = NOTIFYICONDATA
        self.nid = NOTIFYICONDATA()
        self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
        self.nid.uFlags = 0x1 | 0x2  # NIF_ICON | NIF_MESSAGE
        self.nid.szTip = "Virtual Mic\0"

    def _create_default_icon(self):
        """创建纯文本托盘图标"""
        ICON_INFO = ctypes.c_ubyte * (32 * 32 * 4)
        icon_data = ICON_INFO()
        
        # 简单创建一个红色方块图标
        for i in range(32*32):
            icon_data[i*4] = 255   # Red
            icon_data[i*4+3] = 255 # Alpha
        
        return self.user32.CreateIconFromResource(
            ctypes.byref(icon_data), len(icon_data), True, 0x00030000
        )

    def audio_loop(self):
        """音频转发核心"""
        import sounddevice as sd  # 延迟导入
        
        def callback(indata, outdata, *_):
            outdata[:] = indata
            
        with sd.Stream(
            channels=1,
            callback=callback,
            samplerate=44100
        ):
            while self.running:
                sd.sleep(1000)

    def run(self):
        """主运行逻辑"""
        # 隐藏控制台
        self.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )
        
        # 设置图标
        self.nid.hIcon = self._create_default_icon()
        
        # 启动音频线程
        threading.Thread(target=self.audio_loop, daemon=True).start()
        
        # 显示托盘图标
        self.shell32.Shell_NotifyIconW(0x0, ctypes.byref(self.nid))  # NIM_ADD
        
        # 消息循环
        msg = wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))
        
        # 清理
        self.running = False
        self.shell32.Shell_NotifyIconW(0x2, ctypes.byref(self.nid))  # NIM_DELETE

if __name__ == "__main__":
    vm = VirtualMic()
    vm.run()
