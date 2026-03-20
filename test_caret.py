import time
import ctypes
from ctypes import wintypes
import uiautomation as auto
import win32api

# --- Win32 定义 ---
user32 = ctypes.windll.user32
class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND), ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT)
    ]

def get_caret_win32():
    try:
        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)
        hwnd = user32.GetForegroundWindow()
        tid_target = user32.GetWindowThreadProcessId(hwnd, None)
        tid_current = ctypes.windll.kernel32.GetCurrentThreadId()
        
        if tid_target != tid_current:
            user32.AttachThreadInput(tid_current, tid_target, True)
            
        success = user32.GetGUIThreadInfo(tid_target, ctypes.byref(gui_info))
        
        if tid_target != tid_current:
            user32.AttachThreadInput(tid_current, tid_target, False)
            
        if success and gui_info.hwndCaret:
            point = wintypes.POINT(gui_info.rcCaret.left, gui_info.rcCaret.bottom)
            user32.ClientToScreen(gui_info.hwndCaret, ctypes.byref(point))
            return point.x, point.y
    except Exception as e:
        pass
    return 0, 0

def get_caret_uia():
    try:
        element = auto.GetFocusedControl()
        if not element: return 0, 0
        
        # 尝试 TextPattern（VSCode、Word、浏览器）
        pattern = element.GetPattern(auto.PatternId.TextPattern)
        if pattern:
            selections = pattern.GetSelection()
            if selections:
                # 光标是一个退化的选区
                rects = selections[0].GetBoundingRectangles()
                if rects:
                    # rects 是 [left, top, width, height, ...]
                    return int(rects[0] + rects[2]), int(rects[1] + rects[3])
                    
        # 尝试 ValuePattern（简单文本框）
        # ValuePattern 不直接提供光标位置
    except Exception as e:
        pass
    return 0, 0

def main():
    print("=== 光标位置诊断工具 ===")
    print("将焦点移动到不同应用（记事本、VS Code、浏览器）。")
    print("每 1 秒检查一次...\n")
    
    while True:
        mx, my = win32api.GetCursorPos()
        w_x, w_y = get_caret_win32()
        u_x, u_y = get_caret_uia()
        
        print(f"Mouse: ({mx}, {my}) | Win32: ({w_x}, {w_y}) | UIA: ({u_x}, {u_y})")
        time.sleep(1)

if __name__ == "__main__":
    main()
