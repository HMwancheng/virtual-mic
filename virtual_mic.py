import sys
import os
import ctypes
import threading
from ctypes import wintypes
import tempfile

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
        ("szTip", wintypes.WCHAR * 64),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
    ]

# ======================
# Emoji 图标生成器
# ======================
def create_emoji_icon():
    """使用系统字体渲染🎤表情为图标"""
    try:
        # 临时创建ICO文件
        tmp_ico = os.path.join(tempfile.gettempdir(), "vm_icon.ico")
        
        # 方法1：使用系统Emoji字体（需预装）
        if sys.platform == "win32":
            import win32gui  # pylint: disable=import-error
            hdc = win32gui.CreateDC("DISPLAY", None, None)
            lf = win32gui.LOGFONT()
            lf.lfFaceName = "Segoe UI Emoji"
            hfont = win32gui.CreateFontIndirect(lf)
            win32gui.SelectObject(hdc, hfont)
            win32gui.DrawText(hdc, "🎤", -1, (0,0,64,64), 0x1 | 0x4)  # DT_CENTER|DT_VCENTER
            win32gui.SaveDC(hdc)
            # 这里简化了实际图标生成过程，真实项目建议使用方法2
            with open(tmp_ico, "wb") as f:
                f.write(b"DummyICOHeader")  # 实际应生成完整ICO文件
            return tmp_ico
        
        # 方法2：备用方案 - 使用字符画
        with open(tmp_ico, "wb") as f:
            f.write(b'\x00\x00\x01\x00\x01\x00\x20\x20\x00\x00\x01\x00\x08\x00\xA8\x08\x00\x00')  # 简化的单色图标
        return tmp_ico
        
    except Exception:
        return None

# ======================
# 音频转发核心
# ======================
def audio_loop(stop_event):
    import sounddevice as sd
    with sd.Stream(channels=1, callback=lambda i,o,*_: o.__setitem__((), i)):
        while not stop_event.is_set():
            sd.sleep(1000)

# ======================
# 主程序
# ======================
def main():
    if sys.platform != "win32":
        ctypes.windll.user32.MessageBoxW(0, "仅支持Windows系统", "错误", 0x10)
        return

    # 隐藏控制台
    ctypes.windll.user32.ShowWindow(
        ctypes.windll.kernel32.GetConsoleWindow(), 0
    )

    # 创建托盘图标
    shell32 = ctypes.windll.shell32
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    
    nid = NOTIFYICONDATA()
    nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
    nid.uFlags = 0x1 | 0x2  # NIF_ICON | NIF_MESSAGE
    nid.szTip = "Virtual Mic\0"
    
    # 生成并加载Emoji图标
    icon_path = create_emoji_icon()
    if icon_path and os.path.exists(icon_path):
        nid.hIcon = user32.LoadImageW(
            0, icon_path, 1, 0, 0, 0x10|0x20  # LR_LOADFROMFILE|LR_DEFAULTSIZE
        )
    else:
        # 备用方案：创建纯色图标
        nid.hIcon = user32.CreateIcon(
            user32.GetWindowDC(0), 32, 32, 1, 32, 
            (ctypes.c_ubyte * 128)(*([255]*128)), 
            (ctypes.c_ubyte * 128)(*([0]*128))
    
    # 启动音频线程
    stop_event = threading.Event()
    audio_thread = threading.Thread(
        target=audio_loop, args=(stop_event,), daemon=True
    )
    audio_thread.start()
    
    # 显示托盘图标
    shell32.Shell_NotifyIconW(0x0, ctypes.byref(nid))  # NIM_ADD
    
    try:
        # 消息循环
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        stop_event.set()
        shell32.Shell_NotifyIconW(0x2, ctypes.byref(nid))  # NIM_DELETE
        if 'hIcon' in locals():
            gdi32.DeleteObject(nid.hIcon)
        if icon_path and os.path.exists(icon_path):
            try: os.remove(icon_path)
            except: pass

if __name__ == "__main__":
    main()
