import time
import ctypes
from ctypes import wintypes
import uiautomation as auto
import win32api

# --- Win32 Definitions ---
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
        
        # Try TextPattern (VSCode, Word, Browsers)
        pattern = element.GetPattern(auto.PatternId.TextPattern)
        if pattern:
            selections = pattern.GetSelection()
            if selections:
                # Cursor is a degenerate selection
                rects = selections[0].GetBoundingRectangles()
                if rects:
                    # rects is [left, top, width, height, ...]
                    return int(rects[0] + rects[2]), int(rects[1] + rects[3])
                    
        # Try ValuePattern (Simple Textboxes)
        # ValuePattern doesn't give cursor pos directly easily.
    except Exception as e:
        pass
    return 0, 0

def main():
    print("=== Caret Tracking Diagnostic Tool ===")
    print("Move focus to different apps (Notepad, VS Code, Browser).")
    print("Checking every 1 second...\n")
    
    while True:
        mx, my = win32api.GetCursorPos()
        w_x, w_y = get_caret_win32()
        u_x, u_y = get_caret_uia()
        
        print(f"Mouse: ({mx}, {my}) | Win32: ({w_x}, {w_y}) | UIA: ({u_x}, {u_y})")
        time.sleep(1)

if __name__ == "__main__":
    main()
