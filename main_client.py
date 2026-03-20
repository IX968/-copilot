import sys
import threading
from PyQt6.QtWidgets import QApplication

from input_hook import InputHook
from ui_overlay import GhostTextOverlay
# from ctx_provider import ContextProvider # 已移动以防止 DPI 冲突
from inference_engine import InferenceEngine

import time

import sys
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from input_hook import InputHook
from ui_overlay import GhostTextOverlay
# from ctx_provider import ContextProvider # 已移动以防止 DPI 冲突
from inference_engine import InferenceEngine

import time

class GlobalCopilotApp(QObject):
    # 定义用于线程安全 UI 更新的信号
    # 参数：(text, x, y)
    show_suggestion_signal = pyqtSignal(str, int, int)
    hide_suggestion_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 1. 尽快初始化 Qt（设置 DPI 感知）
        self.app = QApplication(sys.argv)
        
        # 2. 组件初始化
        self.overlay = GhostTextOverlay()
        self.input_hook = InputHook()
        
        # 3. 在 Qt 获取 DPI 上下文后导入 UIA
        try:
            from ctx_provider import ContextProvider
            self.ctx_provider = ContextProvider()
        except Exception as e:
            print(f"警告：上下文提供者初始化失败：{e}")
            self.ctx_provider = None

        self.backend = InferenceEngine()
        
        # 连接信号到 UI 槽函数
        self.show_suggestion_signal.connect(self.overlay.update_ghost_text)
        self.hide_suggestion_signal.connect(self.overlay.hide)
        
        # 状态
        self.current_suggestion = ""
        self.last_context = ""

    def initialize(self):
        print("正在初始化全局 Copilot...")

        # 1. 加载后端（阻塞，但启动时没问题）
        if not self.backend.load_model():
            print("错误：后端加载失败，正在退出。")
            sys.exit(1)

        # 2. 设置输入钩子
        self.input_hook.set_callbacks(
            on_trigger=self.trigger_completion,
            on_accept=self.accept_suggestion,
            on_reject=self.reject_suggestion
        )
        self.input_hook.start()
        
        print("系统已就绪。在任何应用中开始打字...")

        # 3. 启动 UI 循环
        sys.exit(self.app.exec())

    def trigger_completion(self):
        # 运行在后台线程上（InputHook）

        # 1. 获取上下文
        if not self.ctx_provider:
             return

        context, x, y, app_name = self.ctx_provider.get_focused_context()
        if not context or len(context.strip()) == 0:
            return

        print(f"在 {app_name} 中触发。上下文长度：{len(context)} 位置：({x},{y})")

        # 2. 生成
        suggestion = self.backend.generate_completion(context, max_new_tokens=16)
        
        if suggestion and len(suggestion.strip()) > 0:
            if "\n" in suggestion:
                suggestion = suggestion.split("\n")[0]
            
            self.current_suggestion = suggestion
            self.input_hook.set_suggestion_visible(True)
            
            # 向主线程发送信号
            self.show_suggestion_signal.emit(suggestion, x, y)
        else:
            self.reject_suggestion()

    def accept_suggestion(self):
        # 用户按下 Tab
        if self.current_suggestion:
            import keyboard
            keyboard.write(self.current_suggestion)
            self.reject_suggestion() # 接受后隐藏

    def reject_suggestion(self):
        # 用户按下 Esc 或打字（取消）
        self.input_hook.set_suggestion_visible(False)
        self.current_suggestion = ""
        # 向主线程发送信号
        self.hide_suggestion_signal.emit()

if __name__ == "__main__":
    copilot = GlobalCopilotApp()
    copilot.initialize()
