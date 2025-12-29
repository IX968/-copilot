import sys
import threading
from PyQt6.QtWidgets import QApplication

from input_hook import InputHook
from ui_overlay import GhostTextOverlay
# from ctx_provider import ContextProvider # MOVED TO PREVENT DPI CONFLICT
from inference_engine import InferenceEngine

import time

import sys
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from input_hook import InputHook
from ui_overlay import GhostTextOverlay
# from ctx_provider import ContextProvider # MOVED TO PREVENT DPI CONFLICT
from inference_engine import InferenceEngine

import time

class GlobalCopilotApp(QObject):
    # Dfine Signal for Thread-Safe UI Updates
    # arguments: (text, x, y)
    show_suggestion_signal = pyqtSignal(str, int, int)
    hide_suggestion_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 1. Initialize Qt ASAP (Sets DPI Awareness)
        self.app = QApplication(sys.argv)
        
        # 2. Components
        self.overlay = GhostTextOverlay()
        self.input_hook = InputHook()
        
        # 3. Import UIA after Qt has claimed DPI context
        try:
            from ctx_provider import ContextProvider
            self.ctx_provider = ContextProvider()
        except Exception as e:
            print(f"Warning: Context Provider Init Failed: {e}")
            self.ctx_provider = None

        self.backend = InferenceEngine()
        
        # Connect Signals to UI Slots
        self.show_suggestion_signal.connect(self.overlay.update_ghost_text)
        self.hide_suggestion_signal.connect(self.overlay.hide)
        
        # State
        self.current_suggestion = ""
        self.last_context = ""

    def initialize(self):
        print("Initializing Global Copilot...")
        
        # 1. Load Backend (Blocking, but okay for startup)
        if not self.backend.load_model():
            print("Error: Backend failed to load. Exiting.")
            sys.exit(1)

        # 2. Setup Input Hooks
        self.input_hook.set_callbacks(
            on_trigger=self.trigger_completion,
            on_accept=self.accept_suggestion,
            on_reject=self.reject_suggestion
        )
        self.input_hook.start()
        
        print("System Ready. Start typing in any app...")
        
        # 3. Start UI Loop
        sys.exit(self.app.exec())

    def trigger_completion(self):
        # RUNNING ON BACKGROUND THREAD (InputHook)
        
        # 1. Get Context
        if not self.ctx_provider:
             return

        context, x, y, app_name = self.ctx_provider.get_focused_context()
        if not context or len(context.strip()) == 0:
            return

        print(f"Triggered in {app_name}. CtxLen: {len(context)} Pos: ({x},{y})")
        
        # 2. Generate
        suggestion = self.backend.generate_completion(context, max_new_tokens=16)
        
        if suggestion and len(suggestion.strip()) > 0:
            if "\n" in suggestion:
                suggestion = suggestion.split("\n")[0]
            
            self.current_suggestion = suggestion
            self.input_hook.set_suggestion_visible(True)
            
            # Emit Signal to Main Thread
            self.show_suggestion_signal.emit(suggestion, x, y)
        else:
            self.reject_suggestion()

    def accept_suggestion(self):
        # User pressed Tab
        if self.current_suggestion:
            import keyboard
            keyboard.write(self.current_suggestion)
            self.reject_suggestion() # Hide after accept

    def reject_suggestion(self):
        # User pressed Esc or Type (Cancel)
        self.input_hook.set_suggestion_visible(False)
        self.current_suggestion = ""
        # Emit Signal to Main Thread
        self.hide_suggestion_signal.emit()

if __name__ == "__main__":
    copilot = GlobalCopilotApp()
    copilot.initialize()
