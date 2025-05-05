import sys
import os
import ctypes
import threading
from ctypes import wintypes
import sounddevice as sd

# ======================
# Windows API 封装
# ======================
class WinTray:
    def __init__(self):
        self.user32 = ctypes.WinDLL('user32')
        self.shell32 = ctypes.WinDLL('shell32')
        
        # 定义结构体
        class NOTIFYICONDATA(ctypes.Structure):
            _fields_ = [
                ('cbSize', wintypes.DWORD),
                ('hWnd', wintypes.HWND),
                ('uID', wintypes.UINT),
                ('uFlags', wintypes.UINT),
                ('uCallbackMessage', wintypes.UINT),
                ('hIcon', wintypes.HICON),
                ('szTip', wintypes.WCHAR * 128),
                ('dwState', wintypes.DWORD),
                ('dwStateMask', wintypes.DWORD),
                ('szInfo', wintypes.WCHAR * 256),
                ('uTimeout', wintypes.UINT)
            ]
        
        self.NOTIFYICONDATA = NOTIFYICONDATA
        self.menu_items = {
            1001: "选择输入设备",
            1002: "退出"
        }
        
        # 创建隐藏窗口接收消息
        self.window_class = "VirtualMicTray"
        self._register_window_class()
        self.hwnd = self.user32.CreateWindowExW(
            0, self.window_class, None, 0, 0, 0, 0, 0, 0, 0, 0, None
        )
        
        # 初始化托盘图标
        self.nid = NOTIFYICONDATA()
        self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
        self.nid.hWnd = self.hwnd
        self.nid.uFlags = 0x1 | 0x2 | 0x4  # NIF_ICON|NIF_MESSAGE|NIF_TIP
        self.nid.uCallbackMessage = 0x400 + 1
        self.nid.szTip = "虚拟麦克风\0"
        
        # 创建默认图标
        self._create_default_icon()

    def _register_window_class(self):
        """注册窗口类"""
        wnd_class = wintypes.WNDCLASSW()
        wnd_class.lpfnWndProc = ctypes.WINFUNCTYPE(
            wintypes.LRESULT, wintypes.HWND, wintypes.UINT, 
            wintypes.WPARAM, wintypes.LPARAM
        )(self._window_proc)
        wnd_class.lpszClassName = self.window_class
        self.user32.RegisterClassW(ctypes.byref(wnd_class))

    def _window_proc(self, hwnd, msg, wparam, lparam):
        """窗口消息处理"""
        if msg == self.nid.uCallbackMessage:
            if lparam == 0x0205:  # 右键单击
                self._show_menu()
        elif msg == 0x0111:  # 菜单命令
            if wparam == 1001:  # 选择设备
                self._select_input_device()
            elif wparam == 1002:  # 退出
                self.user32.PostQuitMessage(0)
        return self.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _create_default_icon(self):
        """创建系统默认图标"""
        icon_data = (ctypes.c_ubyte * (32*32*4))()
        for i in range(32*32):
            icon_data[i*4] = 255    # Red
            icon_data[i*4+3] = 255  # Alpha
        self.nid.hIcon = self.user32.CreateIconFromResource(
            ctypes.byref(icon_data), len(icon_data), True, 0x00030000
        )

    def _show_menu(self):
        """显示右键菜单"""
        hmenu = self.user32.CreatePopupMenu()
        
        # 添加菜单项
        for item_id, text in self.menu_items.items():
            self.user32.AppendMenuW(
                hmenu, 0x0, item_id, text
            )
        
        # 获取光标位置
        point = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        
        # 显示菜单
        self.user32.SetForegroundWindow(self.hwnd)
        self.user32.TrackPopupMenuEx(
            hmenu, 0x100, point.x, point.y, self.hwnd, None
        )
        self.user32.DestroyMenu(hmenu)

    def _select_input_device(self):
        """显示设备选择对话框"""
        devices = sd.query_devices()
        input_devices = [
            f"{i}: {d['name']}" 
            for i, d in enumerate(devices) 
            if d['max_input_channels'] > 0
        ]
        
        selected = ctypes.c_int(0)
        if self.user32.MessageBoxW(
            0,
            "可用输入设备:\n" + "\n".join(input_devices) + "\n\n输入设备编号:",
            "选择输入源",
            0x40 | 0x1  # MB_ICONINFORMATION | MB_OKCANCEL
        ) == 1:  # OK
            print("TODO: 实现设备切换逻辑")

    def show(self):
        """显示托盘图标"""
        self.shell32.Shell_NotifyIconW(0x0, ctypes.byref(self.nid))  # NIM_ADD
        
        # 消息循环
        msg = wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))
        
        # 退出清理
        self.shell32.Shell_NotifyIconW(0x2, ctypes.byref(self.nid))  # NIM_DELETE

# ======================
# 音频处理核心
# ======================
class AudioEngine:
    def __init__(self):
        self.current_device = sd.default.device[0]
        self.running = True

    def start_stream(self):
        """启动音频流"""
        def callback(indata, outdata, frames, time, status):
            outdata[:] = indata
        
        self.stream = sd.Stream(
            device=(self.current_device, None),
            channels=1,
            callback=callback,
            samplerate=44100
        )
        self.stream.start()

    def change_device(self, device_id):
        """切换输入设备"""
        self.stream.stop()
        self.current_device = device_id
        self.start_stream()

# ======================
# 主程序
# ======================
def main():
    if sys.platform != "win32":
        ctypes.windll.user32.MessageBoxW(0, "仅支持Windows", "错误", 0x10)
        return
    
    # 初始化音频引擎
    audio = AudioEngine()
    audio.start_stream()
    
    # 显示托盘图标
    tray = WinTray()
    tray.show()

    # 退出时停止音频流
    if hasattr(audio, 'stream'):
        audio.stream.stop()

if __name__ == "__main__":
    main()
