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
        # 1. Frameless, Transparent, Always on Top, Tool (no taskbar icon)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus # Transparent to clicks? Maybe. For now, let it accept clicks if user wants.
            # Actually, ghost text should be "click-through" usually, or at least not steal focus.
            # But we need it to be visible.
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating) # Don't steal focus when showing

        # 2. Font Setup
        self.font_family = "Consolas"
        self.font_size = 12
        self.qfont = QFont(self.font_family, self.font_size)
        
        # 3. Label Setup
        self.label = QLabel(self)
        self.label.setFont(self.qfont)
        # Debug Mode: Dark Gray Background, White Text
        self.label.setStyleSheet("color: #aaaaaa; background-color: #333333; border: 1px solid #555555;")
        self.label.setAutoFillBackground(True) # Ensure background is painted

        # Window Styling for Visibility
        self.setWindowOpacity(0.9) # Slight transparency for whole window
        # Remove WA_TranslucentBackground for now to test visibility
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) 

        self.resize(100, 30) # Default size
        self.hide()

    def update_ghost_text(self, text, x, y, font_size=None):
        """
        Update the overlay content and position.
        x, y: Screen coordinates of the caret (cursor).
        """
        if not text:
            self.hide()
            return

        self.suggestion_text = text
        self.label.setText(text)
        self.label.adjustSize()
        
        if font_size and font_size != self.font_size:
            self.font_size = font_size
            self.qfont.setPointSize(font_size)
            self.label.setFont(self.qfont)
            self.label.adjustSize()

        # Position just slightly to the right of cursor
        # Note: We might need to adjust Y to align baselines
        self.move(x + 2, y) 
        self.resize(self.label.size())
        self.show()

if __name__ == '__main__':
    # Test Stub
    app = QApplication(sys.argv)
    overlay = GhostTextOverlay()
    
    # Simulate a caret position (e.g., middle of screen)
    overlay.update_ghost_text("print('Hello World') # This is AI suggestion", 500, 500, 14)
    
    sys.exit(app.exec())
