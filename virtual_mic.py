import sys
import ctypes
import threading
from ctypes import wintypes

class VirtualMic:
    def __init__(self):
        self.running = True
        self._setup_windows_api()

    def _setup_windows_api(self):
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
        self.nid.uFlags = 0x1  # 仅使用NIF_MESSAGE
        self.nid.uCallbackMessage = 0x400 + 1
        self.nid.szTip = "Virtual Mic\0"

    def _create_default_icon(self):
        """创建系统默认图标"""
        # 使用系统标准图标
        ICON_INFO = (ctypes.c_ubyte * (32 * 32 * 4))()
        return self.user32.CreateIconFromResource(
            ctypes.byref(ICON_INFO), len(ICON_INFO), True, 0x00030000
        )

    def audio_loop(self):
        """极简音频转发"""
        import sounddevice as sd
        def callback(indata, outdata, *_):
            outdata[:] = indata
            
        with sd.Stream(
            channels=1,
            callback=callback,
            samplerate=44100,
            blocksize=1024
        ):
            while self.running:
                sd.sleep(1000)

    def run(self):
        """主控制逻辑"""
        # 隐藏控制台
        self.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )
        
        # 设置图标
        self.nid.hIcon = self._create_default_icon()
        
        # 启动音频线程
        threading.Thread(target=self.audio_loop, daemon=True).start()
        
        # 显示托盘图标
        self.shell32.Shell_NotifyIconW(0x0, ctypes.byref(self.nid))
        
        # 消息循环
        msg = wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
            if msg.message == self.nid.uCallbackMessage:
                if msg.lParam == 0x0205:  # 右键点击
                    self.running = False
                    self.user32.PostQuitMessage(0)
            
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))
        
        # 清理
        self.shell32.Shell_NotifyIconW(0x2, ctypes.byref(self.nid))

if __name__ == "__main__":
    if sys.platform != "win32":
        ctypes.windll.user32.MessageBoxW(0, "仅支持Windows系统", "错误", 0x10)
        sys.exit(1)
    
    vm = VirtualMic()
    vm.run()
