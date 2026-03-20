import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette

class GhostTextOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.suggestion_text = ""

    def initUI(self):
        # 1. 无边框、透明、置顶、工具窗口（无任务栏图标）
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus # 对点击透明？也许。暂时让它接受点击。
            # 实际上，幽灵文本通常应该是"可点击穿透的"，或者至少不抢占焦点。
            # 但我们需要它可见。
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating) # 显示时不抢占焦点

        # 2. 字体设置
        self.font_family = "Consolas"
        self.font_size = 12
        self.qfont = QFont(self.font_family, self.font_size)
        
        # 3. 标签设置
        self.label = QLabel(self)
        self.label.setFont(self.qfont)
        # 调试模式：深灰背景，白色文字
        self.label.setStyleSheet("color: #aaaaaa; background-color: #333333; border: 1px solid #555555;")
        self.label.setAutoFillBackground(True) # 确保背景被绘制

        # 窗口样式以确保可见性
        self.setWindowOpacity(0.9) # 整个窗口轻微透明
        # 暂时移除 WA_TranslucentBackground 以测试可见性
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) 

        self.resize(100, 30) # 默认大小
        self.hide()

    def update_ghost_text(self, text, x, y, font_size=None):
        """
        更新叠加层内容和位置。
        x, y: 光标的屏幕坐标。
        """
        if not text:
            self.hide()
            return

        self.suggestion_text = text
        self.label.setText(text)
        self.label.adjustSize()
        self.resize(self.label.size()) # 调整窗口大小以适应标签

        if font_size and font_size != self.font_size:
            self.font_size = font_size
            self.qfont.setPointSize(font_size)
            self.label.setFont(self.qfont)
            self.label.adjustSize()
            self.resize(self.label.size()) # 字体大小改变后重新调整

        # 修复：将物理坐标（来自 Win32）转换为逻辑坐标（用于 Qt）
        # 用户使用高 DPI（如 150%），所以 Qt 会按比例放大 'move(x,y)'。
        # 我们需要除以比率来抵消这种缩放。
        ratio = self.devicePixelRatio()
        if ratio == 0: ratio = 1
        
        logical_x = int(x / ratio)
        logical_y = int(y / ratio)
        
        # 定位在光标右侧稍偏位置
        self.move(logical_x, logical_y)
        self.resize(self.label.size())
        self.show()

if __name__ == '__main__':
    # 测试桩代码
    app = QApplication(sys.argv)
    overlay = GhostTextOverlay()
    
    # 模拟光标位置（如屏幕中央）
    overlay.update_ghost_text("print('Hello World') # 这是 AI 建议", 500, 500, 14)
    
    sys.exit(app.exec())
