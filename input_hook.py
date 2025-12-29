import keyboard
import time
import threading
from typing import Callable

class InputHook:
    def __init__(self):
        self.typing_buffer = [] # Store recent keys
        self.last_type_time = 0
        self.debounce_timer = None
        self.is_paused = False
        
        # Callbacks
        self.on_trigger_completion: Callable = None
        self.on_accept_completion: Callable = None
        self.on_reject_completion: Callable = None
        
        # State
        self.suggestion_visible = False

    def start(self):
        # Hook global events
        keyboard.on_release(self._on_key_release)
        # Tab and Esc need specific handling to intercept
        # Note: Suppress=True might block keys globally, be careful.
        # Ideally, we only suppress if suggestion is visible.
        keyboard.add_hotkey('tab', self._on_tab, suppress=True, trigger_on_release=False)
        keyboard.add_hotkey('esc', self._on_esc, suppress=False, trigger_on_release=False)
        print("Input Hook Started.")

    def set_callbacks(self, on_trigger, on_accept, on_reject):
        self.on_trigger_completion = on_trigger
        self.on_accept_completion = on_accept
        self.on_reject_completion = on_reject

    def _on_key_release(self, event):
        if self.is_paused:
            return

        name = event.name
        
        # Ignore modifiers and special keys for triggering
        if name in ['shift', 'ctrl', 'alt', 'caps lock', 'tab', 'esc']:
            return

        self.last_type_time = time.time()
        
        # Simple Debounce Logic: 
        # If user stops typing for X ms, trigger completion
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        # Wait 300ms after last keystroke to trigger AI
        self.debounce_timer = threading.Timer(0.3, self._trigger_event)
        self.debounce_timer.start()

    def _trigger_event(self):
        if self.on_trigger_completion:
            self.on_trigger_completion()

    def _on_tab(self):
        if self.suggestion_visible:
            print("Tab pressed: Accepting suggestion")
            if self.on_accept_completion:
                self.on_accept_completion()
        else:
            # Pass Tab through (Re-send it since we intercepted it)
            # Unhook temporarily to avoid recursion
            keyboard.remove_hotkey('tab')
            keyboard.send('tab')
            keyboard.add_hotkey('tab', self._on_tab, suppress=True, trigger_on_release=False)

    def _on_esc(self):
        if self.suggestion_visible:
            print("Esc pressed: Rejecting suggestion")
            if self.on_reject_completion:
                self.on_reject_completion()

    def set_suggestion_visible(self, visible):
        self.suggestion_visible = visible

if __name__ == "__main__":
    # Test stub
    hook = InputHook()
    hook.set_callbacks(
        lambda: print("Trigger AI!"),
        lambda: print("Accepted!"),
        lambda: print("Rejected!")
    )
    hook.start()
    hook.set_suggestion_visible(True) # Test tab interception
    
    print("Hook running. Press keys, wait, or press Tab...")
    keyboard.wait()
