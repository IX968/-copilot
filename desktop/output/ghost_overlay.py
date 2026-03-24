"""
幽灵文本悬浮窗
使用 PyQt6 显示半透明的 AI 建议文本
"""
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class GhostOverlay(QMainWindow):
    """
    幽灵文本悬浮窗

    功能:
    - 透明背景，置顶显示
    - 半透明灰色文本
    - 自动调整大小和位置
    """

    def __init__(
        self,
        alpha: float = 0.8,
        font_size: int = 14,
        color: str = "#aaaaaa"
    ):
        """
        初始化悬浮窗

        Args:
            alpha: 透明度 (0.1-1.0)
            font_size: 字体大小
            color: 文字颜色（十六进制）
        """
        super().__init__()

        self.alpha = alpha
        self.font_size = font_size
        self.color = color
        self._current_text = ""

        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        # 无边框、置顶、透明窗口、鼠标穿透
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # 创建标签
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label.setWordWrap(False)

        # 设置样式
        self._update_style()

        # 初始隐藏
        self.hide()

    def _update_style(self):
        """更新样式"""
        # 计算背景色（深色半透明）
        bg_color = f"rgba(20, 20, 30, {int(200 * self.alpha)})"

        self.label.setStyleSheet(f"""
            QLabel {{
                color: {self.color};
                background-color: {bg_color};
                font-size: {self.font_size}px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                padding: 4px 8px;
                border-radius: 4px;
            }}
        """)

        font = QFont("Consolas", self.font_size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.label.setFont(font)

    def update_ghost_text(self, text: str, x: int = None, y: int = None):
        """
        更新幽灵文本

        Args:
            text: 要显示的文本
            x: X 坐标（屏幕位置）
            y: Y 坐标（屏幕位置）
        """
        if not text:
            self.hide_ghost_text()
            return

        self._current_text = text

        # 更新标签文本
        self.label.setText(text)
        self.label.adjustSize()

        # 设置大小
        self.setFixedSize(
            self.label.width() + 20,
            self.label.height() + 10
        )

        # 修复 DPI 缩放带来的坐标越界问题
        # 与其处理容易出错的物理到逻辑的转换，在 PyQt6 中最稳妥的方式是
        # 直接拿 Qt 提供的全局逻辑光标位置 QCursor.pos()。
        # 这样无论跨多少个不同缩放比例和分辨率的屏幕，都能丝滑定位。
        from PyQt6.QtGui import QCursor
        cursor_pos = QCursor.pos()

        # 在鼠标右下角偏移15像素显示气泡，以防遮挡鼠标
        self.move(cursor_pos.x() + 15, cursor_pos.y() + 15)

        # 显示
        self.show()

    def hide_ghost_text(self):
        """隐藏幽灵文本"""
        self.hide()
        self._current_text = ""

    def get_current_text(self) -> str:
        """获取当前显示的文本"""
        return self._current_text

    def set_alpha(self, alpha: float):
        """
        设置透明度

        Args:
            alpha: 透明度 (0.1-1.0)
        """
        self.alpha = max(0.1, min(1.0, alpha))
        self._update_style()

    def set_color(self, color: str):
        """
        设置文字颜色

        Args:
            color: 十六进制颜色
        """
        self.color = color
        self._update_style()

    def set_font_size(self, size: int):
        """
        设置字体大小

        Args:
            size: 字体大小
        """
        self.font_size = max(8, min(72, size))
        self._update_style()


# 全局悬浮窗实例
_overlay: GhostOverlay = None


def get_ghost_overlay() -> GhostOverlay:
    """获取全局悬浮窗实例"""
    global _overlay
    if _overlay is None:
        # 确保 QApplication 已初始化
        if not QApplication.instance():
            app = QApplication(sys.argv)
        _overlay = GhostOverlay()
    return _overlay
