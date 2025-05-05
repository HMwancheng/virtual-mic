import sys
import ctypes
import threading
from ctypes import wintypes

class VirtualMic:
    def __init__(self):
        self.running = True
        self._setup_api()

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
        
        self.nid = NOTIFYICONDATA()
        self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
        self.nid.uFlags = 0x1  # NIF_MESSAGE
        self.nid.uCallbackMessage = 0x400 + 1
        self.nid.szTip = "Virtual Mic\0"

    def _audio_callback(self, indata, outdata):
        """替代NumPy的纯Python音频转发"""
        for i in range(len(outdata)):
            outdata[i] = indata[i]

    def audio_loop(self):
        """音频处理线程"""
        import sounddevice as sd
        with sd.Stream(
            channels=1,
            dtype='float32',
            callback=lambda i,o,f,t,s: self._audio_callback(i, o),
            samplerate=44100
        ):
            while self.running:
                sd.sleep(1000)

    def run(self):
        """主程序"""
        # 隐藏控制台
        self.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )
        
        # 启动音频线程
        threading.Thread(target=self.audio_loop, daemon=True).start()
        
        # 显示托盘图标
        self.shell32.Shell_NotifyIconW(0x0, ctypes.byref(self.nid))
        
        # 消息循环
        msg = wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))
        
        # 清理
        self.running = False
        self.shell32.Shell_NotifyIconW(0x2, ctypes.byref(self.nid))

if __name__ == "__main__":
    if sys.platform != "win32":
        ctypes.windll.user32.MessageBoxW(0, "仅支持Windows", "错误", 0x10)
        sys.exit(1)
    
    VirtualMic().run()
