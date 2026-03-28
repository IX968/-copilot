"""
全局键盘钩子（带防抖机制）
"""
import threading
import time
from typing import Callable, Optional

import keyboard

from app.config import config


class InputHook:
    """
    全局键盘钩子

    功能:
    - 监听全局键盘事件
    - 防抖机制（用户停顿后触发）
    - Tab 接受补全，Esc 拒绝补全
    """

    def __init__(
        self,
        on_trigger: Optional[Callable] = None,
        on_accept: Optional[Callable] = None,
        on_reject: Optional[Callable] = None,
        has_pending: Optional[Callable] = None,
        debounce_ms: int = None
    ):
        """
        初始化键盘钩子

        Args:
            on_trigger: 防抖后触发补全的回调
            on_accept: 接受补全的回调
            on_reject: 拒绝补全的回调
            has_pending: 查询是否有待处理补全的回调（用于条件性拦截 Tab）
            debounce_ms: 防抖时间（毫秒），默认从配置读取
        """
        self.on_trigger = on_trigger
        self.on_accept = on_accept
        self.on_reject = on_reject
        self.has_pending = has_pending
        self.debounce_ms = debounce_ms or config.get('trigger', 'debounce_ms', default=300)
        self.accept_key = config.get('trigger', 'accept_key', default='tab')
        self.reject_key = config.get('trigger', 'reject_key', default='esc')

        self._debounce_timer: Optional[threading.Timer] = None
        self._last_key_time = 0
        self._is_running = False

    def start(self):
        """启动键盘钩子"""
        if self._is_running:
            print("[InputHook] 已经在运行")
            return

        print(f"[InputHook] 启动，防抖时间：{self.debounce_ms}ms")

        # 监听所有按键
        keyboard.hook(self._on_key_event, suppress=False)

        # 监听接受键（Tab）— suppress=True 拦截按键，回调内决定是消耗还是放行
        keyboard.on_press_key(self.accept_key, self._on_accept_key, suppress=True)

        # 监听拒绝键（Esc）
        keyboard.on_press_key(self.reject_key, self._on_reject_key, suppress=False)

        self._is_running = True
        print("[InputHook] 已就绪")

    def stop(self):
        """停止键盘钩子"""
        if not self._is_running:
            return

        keyboard.unhook_all()

        if self._debounce_timer:
            self._debounce_timer.cancel()
            self._debounce_timer = None

        self._is_running = False
        print("[InputHook] 已停止")

    def _on_key_event(self, event):
        """
        按键事件处理

        Args:
            event: 键盘事件
        """
        # 忽略释放事件
        if not event.event_type == keyboard.KEY_DOWN:
            return

        # 忽略修饰键
        if event.name in ['shift', 'ctrl', 'alt', 'win', 'caps_lock']:
            return

        self._last_key_time = time.time()

        # 取消之前的定时器
        if self._debounce_timer:
            self._debounce_timer.cancel()

        # 创建新的定时器
        self._debounce_timer = threading.Timer(
            self.debounce_ms / 1000.0,
            self._trigger_completion
        )
        self._debounce_timer.start()

    def _trigger_completion(self):
        """触发 AI 补全（防抖后）"""
        print("[InputHook] 触发补全请求")

        if self.on_trigger:
            try:
                self.on_trigger()
            except Exception as e:
                print(f"[InputHook] 触发回调失败：{e}")

    def _on_accept_key(self, event):
        """
        接受补全键（Tab）

        suppress=True 下，返回 False 拦截按键，返回 True 放行到应用。
        仅当有待处理补全时拦截 Tab 并执行接受，否则原样放行。
        """
        # 无待处理补全 → 放行 Tab 到应用（正常 Tab 行为）
        if not (self.has_pending and self.has_pending()):
            return True

        # 有待处理补全 → 拦截 Tab，执行接受
        if self._debounce_timer:
            self._debounce_timer.cancel()
            self._debounce_timer = None

        print(f"[InputHook] 接受键按下：{self.accept_key}")

        if self.on_accept:
            try:
                self.on_accept()
            except Exception as e:
                print(f"[InputHook] 接受回调失败：{e}")

        return False  # 拦截 Tab，不让它到达应用

    def _on_reject_key(self, event):
        """
        拒绝补全键（Esc）

        Args:
            event: 键盘事件
        """
        # 取消待处理的触发
        if self._debounce_timer:
            self._debounce_timer.cancel()
            self._debounce_timer = None

        print(f"[InputHook] 拒绝键按下：{self.reject_key}")

        if self.on_reject:
            try:
                self.on_reject()
            except Exception as e:
                print(f"[InputHook] 拒绝回调失败：{e}")

    def set_debounce(self, debounce_ms: int):
        """
        设置防抖时间

        Args:
            debounce_ms: 防抖时间（毫秒）
        """
        self.debounce_ms = debounce_ms
        print(f"[InputHook] 防抖时间更新：{debounce_ms}ms")

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
