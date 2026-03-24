"""
上下文提供者
获取当前应用程序的编辑上下文和光标位置
"""
import uiautomation as auto
from typing import Tuple, Optional


class ContextProvider:
    """
    上下文提供者

    职责:
    - 获取当前焦点元素的文本内容
    - 获取光标/鼠标位置
    - 识别应用名称
    """

    def __init__(self):
        """初始化上下文提供者"""
        self.offset_x = 15  # 光标 X 偏移
        self.offset_y = 15  # 光标 Y 偏移

    def get_focused_context(self) -> Tuple[Optional[str], int, int, str]:
        """
        获取当前焦点上下文

        Returns:
            Tuple[Optional[str], int, int, str]:
                (文本内容，光标 X, 光标 Y, 应用名称)
        """
        try:
            # 1. 获取焦点控件
            element = auto.GetFocusedControl()
            if not element:
                print("[ContextProvider] 无焦点元素")
                return None, 0, 0, "Unknown"

            # 2. 获取应用名称
            app_name = self._get_app_name(element)

            # 3. 获取光标位置（使用鼠标位置）
            caret_x, caret_y = self._get_cursor_position()

            # 4. 获取文本内容
            text_context = self._get_text_content(element)

            return text_context, caret_x, caret_y, app_name

        except Exception as e:
            print(f"[ContextProvider] 错误：{e}")
            return None, 0, 0, "Error"

    def _get_app_name(self, element) -> str:
        """
        获取应用名称

        Args:
            element: UIA 元素

        Returns:
            str: 应用名称
        """
        try:
            import psutil
            pid = element.ProcessId
            process = psutil.Process(pid)
            app_name = process.name()

            # 标注使用鼠标位置
            try:
                import win32api
                win32api.GetCursorPos()  # 测试是否可用
                app_name = f"{app_name} (Mouse)"
            except:
                pass

            return app_name

        except Exception:
            return "UnknownApp"

    def _get_cursor_position(self) -> Tuple[int, int]:
        """
        获取光标位置

        使用鼠标位置 + 偏移作为光标位置
        （UIA 光标位置在許多应用中不可靠）

        Returns:
            Tuple[int, int]: (X, Y) 坐标
        """
        try:
            import win32api
            mx, my = win32api.GetCursorPos()
            return mx + self.offset_x, my + self.offset_y
        except Exception:
            return 0, 0

    def _get_text_content(self, element) -> str:
        """
        获取文本内容

        优先级:
        1. ValuePattern（标准文本框）
        2. Name 属性
        3. 返回空字符串

        Args:
            element: UIA 元素

        Returns:
            str: 文本内容
        """
        try:
            # 尝试 ValuePattern
            value_pattern = element.GetPattern(auto.PatternId.ValuePattern)
            if value_pattern:
                text = value_pattern.Value
                if text:
                    return text

            # 尝试 Name 属性
            name = element.Name
            if name:
                return name

            return ""

        except Exception:
            return ""

    def get_context_with_limit(self, max_length: int = 8000) -> Tuple[str, int, int, str]:
        """
        获取限制长度的上下文

        Args:
            max_length: 最大长度

        Returns:
            Tuple[str, int, int, str]: (上下文，X, Y, 应用名)
        """
        text, x, y, app = self.get_focused_context()

        if text and len(text) > max_length:
            # 保留末尾部分
            text = text[-max_length:]

        return text or "", x, y, app or "Unknown"
