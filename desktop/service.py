"""
桌面服务主程序
整合键盘钩子、上下文提供者、幽灵文本悬浮窗
"""
import sys
import time
import threading
import requests
import pyperclip
import keyboard
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from desktop.input.global_hook import InputHook
from desktop.input.context_provider import ContextProvider
from desktop.output.ghost_overlay import GhostOverlay
from app.config import config


class _SignalBridge(QObject):
    """线程安全的信号桥，用于从后台线程更新 UI"""
    show_ghost = pyqtSignal(str, int, int)   # text, x, y
    hide_ghost = pyqtSignal()


class DesktopService:
    """
    桌面补全服务

    职责:
    - 管理键盘钩子
    - 管理幽灵文本悬浮窗
    - 调用 API 获取补全
    - 处理用户接受/拒绝
    """

    def __init__(self, api_url: str = "http://127.0.0.1:7891"):
        """
        初始化桌面服务

        Args:
            api_url: API 服务器地址
        """
        self.api_url = api_url
        self.app: Optional[QApplication] = None
        self.input_hook: Optional[InputHook] = None
        self.ctx_provider: Optional[ContextProvider] = None
        self.overlay: Optional[GhostOverlay] = None
        self._signal_bridge: Optional[_SignalBridge] = None

        self._pending_completion = None  # 当前待处理的补全
        self._completion_context = None  # 补全的上下文
        self._lock = threading.Lock()    # 保护 _pending_completion 的线程锁

    def initialize(self):
        """初始化服务组件"""
        print("[DesktopService] 初始化...")

        # 屏蔽无害的 DPI 感知拒绝访问报错
        import os
        os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

        # 初始化 Qt 应用
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        # 必须设置此属性，防止唯一的一个隐藏窗口导致事件循环直接退出
        self.app.setQuitOnLastWindowClosed(False)

        # 初始化组件
        self.ctx_provider = ContextProvider()
        self.overlay = GhostOverlay(
            alpha=config.get('desktop', 'ghost_text', 'alpha', default=0.8),
            font_size=config.get('desktop', 'ghost_text', 'font_size', default=14),
            color=config.get('desktop', 'ghost_text', 'color', default='#aaaaaa'),
        )

        # 创建信号桥（线程安全的 UI 更新）
        self._signal_bridge = _SignalBridge()
        self._signal_bridge.show_ghost.connect(self.overlay.update_ghost_text)
        self._signal_bridge.hide_ghost.connect(self.overlay.hide_ghost_text)

        # 创建键盘钩子，设置回调
        self.input_hook = InputHook(
            on_trigger=self._on_trigger_completion,
            on_accept=self.accept_completion,
            on_reject=self.reject_completion,
            has_pending=lambda: self._pending_completion is not None,
        )

        print("[DesktopService] 初始化完成")

    def start(self):
        """启动服务"""
        if not hasattr(self, 'app') or self.app is None:
            self.initialize()

        print("[DesktopService] 启动键盘钩子...")
        self.input_hook.start()

        print("[DesktopService] 服务已启动")
        print("[DesktopService] 按 Tab 接受补全，按 Esc 拒绝")

        # 运行 Qt 事件循环
        sys.exit(self.app.exec())

    def stop(self):
        """停止服务"""
        print("[DesktopService] 停止中...")

        if self.input_hook:
            self.input_hook.stop()

        if self.overlay:
            self.overlay.hide_ghost_text()

        if self.app:
            self.app.quit()

        print("[DesktopService] 已停止")

    def _on_trigger_completion(self):
        """触发补全（键盘钩子回调）"""
        print("[DesktopService] 触发补全...")

        # 启动后台线程获取补全
        thread = threading.Thread(target=self._fetch_completion)
        thread.start()

    def _fetch_completion(self):
        """后台获取补全（一次性），完成后显示气泡"""
        try:
            # 获取上下文
            context, caret_x, caret_y, app_name = self.ctx_provider.get_context_with_limit(
                max_length=config.get('desktop', 'context', 'max_length', default=8000)
            )

            if not context or len(context.strip()) < 3:
                print("[DesktopService] 上下文太短，跳过")
                return

            self._completion_context = context

            # 调用一次性生成 API
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "context": context,
                    "max_tokens": config.get('generation', 'max_tokens', default=64),
                    "temperature": config.get('generation', 'temperature', default=0.7),
                    "top_k": config.get('generation', 'top_k', default=40),
                    "top_p": config.get('generation', 'top_p', default=0.9),
                },
                timeout=(5, 120),
            )

            if response.status_code != 200:
                print(f"[DesktopService] API 错误：{response.status_code}")
                return

            data = response.json()
            text = data.get("text", "")
            if not text:
                return

            tokens = data.get("tokens_generated", 0)
            t = data.get("inference_time", 0)
            tps = data.get("tokens_per_second", 0)
            print(f"[DesktopService] 补全完成：{tokens} tokens, {t:.2f}s, {tps:.1f} t/s | {text[:60]}")

            with self._lock:
                self._pending_completion = text

            self._signal_bridge.show_ghost.emit(text, caret_x, caret_y)

        except requests.exceptions.RequestException as e:
            print(f"[DesktopService] API 调用失败：{e}")
        except Exception as e:
            print(f"[DesktopService] 错误：{e}")

    def accept_completion(self):
        """接受当前补全，通过剪贴板插入文本"""
        with self._lock:
            if not self._pending_completion:
                return
            text = self._pending_completion
        print(f"[DesktopService] 接受补全：{text}")

        # 先隐藏幽灵文本
        self._clear_pending()

        # 通过剪贴板 + 模拟 Ctrl+V 插入文本
        try:
            # 保存原有剪贴板内容
            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                original_clipboard = ""

            # 设置补全文本到剪贴板
            pyperclip.copy(text)

            # 短暂延迟确保剪贴板已就绪
            time.sleep(0.05)

            # 模拟 Ctrl+V 粘贴
            keyboard.send('ctrl+v')

            # 恢复原有剪贴板内容（延迟恢复，确保粘贴完成）
            time.sleep(0.1)
            pyperclip.copy(original_clipboard)

        except Exception as e:
            print(f"[DesktopService] 插入文本失败：{e}")

    def reject_completion(self):
        """拒绝当前补全"""
        print("[DesktopService] 拒绝补全")
        self._clear_pending()

    def _clear_pending(self):
        """清除待处理的补全"""
        with self._lock:
            self._pending_completion = None
            self._completion_context = None

        # 通过信号桥在 Qt 主线程中安全隐藏 UI
        if self._signal_bridge:
            self._signal_bridge.hide_ghost.emit()


def main():
    """主函数"""
    api_host = config.get('server', 'host', default='127.0.0.1')
    api_port = config.get('server', 'port', default=7891)
    api_url = f"http://{api_host}:{api_port}"

    print(f"[DesktopService] 连接到 API: {api_url}")

    # 检查 API 是否可用
    try:
        response = requests.get(f"{api_url}/api/health", timeout=2)
        if response.status_code != 200:
            print("[DesktopService] 警告：API 健康检查失败")
    except Exception:
        print("[DesktopService] 警告：无法连接到 API，请确保 API 服务器已启动")

    service = DesktopService(api_url)
    service.start()


if __name__ == "__main__":
    main()
