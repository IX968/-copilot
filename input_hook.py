import keyboard
import time
import threading
from typing import Callable

class InputHook:
    def __init__(self):
        self.typing_buffer = [] # 存储最近的按键
        self.last_type_time = 0
        self.debounce_timer = None
        self.is_paused = False
        
        # 回调函数
        self.on_trigger_completion: Callable = None
        self.on_accept_completion: Callable = None
        self.on_reject_completion: Callable = None
        
        # 状态
        self.suggestion_visible = False

    def start(self):
        # 钩住全局事件
        keyboard.on_release(self._on_key_release)
        # Tab 和 Esc 需要特殊处理以进行拦截
        # 注意：suppress=True 可能会全局阻塞按键，要小心
        # 理想情况下，我们只在建议可见时才阻塞
        keyboard.add_hotkey('tab', self._on_tab, suppress=True, trigger_on_release=False)
        keyboard.add_hotkey('esc', self._on_esc, suppress=False, trigger_on_release=False)
        print("输入钩子已启动。")

    def set_callbacks(self, on_trigger, on_accept, on_reject):
        self.on_trigger_completion = on_trigger
        self.on_accept_completion = on_accept
        self.on_reject_completion = on_reject

    def _on_key_release(self, event):
        if self.is_paused:
            return

        name = event.name
        
        # 忽略修饰键和特殊键以触发补全
        if name in ['shift', 'ctrl', 'alt', 'caps lock', 'tab', 'esc']:
            return

        self.last_type_time = time.time()
        
        # 简单防抖逻辑：
        # 如果用户停止打字 X 毫秒，触发补全
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        # 最后一次按键后等待 300ms 触发 AI
        self.debounce_timer = threading.Timer(0.3, self._trigger_event)
        self.debounce_timer.start()

    def _trigger_event(self):
        if self.on_trigger_completion:
            self.on_trigger_completion()

    def _on_tab(self):
        if self.suggestion_visible:
            print("Tab 按下：接受建议")
            if self.on_accept_completion:
                self.on_accept_completion()
        else:
            # 让 Tab 通过（重新发送它，因为我们拦截了它）
            # 暂时移除钩子以避免递归
            keyboard.remove_hotkey('tab')
            keyboard.send('tab')
            keyboard.add_hotkey('tab', self._on_tab, suppress=True, trigger_on_release=False)

    def _on_esc(self):
        if self.suggestion_visible:
            print("Esc 按下：拒绝建议")
            if self.on_reject_completion:
                self.on_reject_completion()

    def set_suggestion_visible(self, visible):
        self.suggestion_visible = visible

if __name__ == "__main__":
    # 测试桩代码
    hook = InputHook()
    hook.set_callbacks(
        lambda: print("Trigger AI!"),
        lambda: print("Accepted!"),
        lambda: print("Rejected!")
    )
    hook.start()
    hook.set_suggestion_visible(True) # 测试 Tab 拦截
    
    print("钩子运行中。按键盘、等待或按 Tab...")
    keyboard.wait()
