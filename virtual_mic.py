import sounddevice as sd
import sys
import ctypes
import threading
from ctypes import wintypes

# Windows API 定义
NOTIFYICONDATA = ctypes.c_ulong, wintypes.HWND, wintypes.UINT, wintypes.UINT, 
                wintypes.HICON, wintypes.WCHAR * 64

class VirtualMic:
    def __init__(self):
        self.running = True
        self._setup_windows_api()

    def _setup_windows_api(self):
        """初始化Windows托盘API"""
        self.shell32 = ctypes.windll.shell32
        self.user32 = ctypes.windll.user32
        
        self.nid = NOTIFYICONDATA(
            0,                          # cbSize
            0,                          # hWnd
            1000,                       # uID
            0x2 | 0x4,                  # NIF_MESSAGE | NIF_ICON
            0,                          # uCallbackMessage
            0,                          # hIcon
            "Virtual Mic"               # szTip
        )
        self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)

    def audio_loop(self):
        """音频转发核心"""
        def callback(indata, outdata, *_):
            outdata[:] = indata
            
        with sd.Stream(
            channels=1,
            callback=callback,
            samplerate=44100
        ):
            while self.running:
                sd.sleep(1000)

    def show_tray_icon(self):
        """显示托盘图标"""
        WM_LBUTTONDOWN = 0x0201
        msg_map = {WM_LBUTTONDOWN: self._show_menu}
        
        # 创建消息循环
        msg = wintypes.MSG()
        while self.running:
            if self.user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
                if msg.message in msg_map:
                    msg_map[msg.message]()
                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))

    def _show_menu(self):
        """右键菜单"""
        menu = self.user32.CreatePopupMenu()
        self.user32.AppendMenuW(menu, 0x0, 1001, "退出")
        
        pos = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(pos))
        
        self.user32.TrackPopupMenuEx(
            menu, 0x100, pos.x, pos.y, self.nid.hWnd, None
        )

    def run(self):
        """启动程序"""
        # 隐藏控制台
        self.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )
        
        # 启动音频线程
        threading.Thread(target=self.audio_loop, daemon=True).start()
        
        # 显示托盘图标
        self.show_tray_icon()

if __name__ == "__main__":
    vm = VirtualMic()
    vm.run()
