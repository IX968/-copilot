import uiautomation as auto
import time
import pyperclip

class ContextProvider:
    def __init__(self):
        pass

    def get_focused_context(self):
        """
        Returns (text_before_caret, caret_x, caret_y, app_name)
        """
        try:
            element = auto.GetFocusedControl()
            if not element:
                print("No focused element")
                return None, 0, 0, "Unknown"

            # 1. Get Application Name (Fixing AttributeError)
            try:
                pid = element.ProcessId
                import psutil
                process = psutil.Process(pid)
                app_name = process.name()
            except ImportError:
                # Fallback if psutil not installed (though likely is on conda)
                app_name = f"PID:{element.ProcessId}"
            except Exception:
                app_name = "UnknownApp"

            rect = element.BoundingRectangle
            
            # --- REVERTED TO MOUSE POS (STABLE) ---
            # The complex caret detection caused issues/crashes.
            # We revert to solid Mouse positioning for now.
            try:
                import win32api
                caret_x, caret_y = win32api.GetCursorPos()
                caret_x += 10 # Offset
                app_name = f"{app_name} (Mouse)"
            except:
                caret_x, caret_y = 0, 0

            # 3. Get Context Text (Essential for Copilot) (Essential for Copilot)
            # Basic implementation: specific to standard Edit controls
            text_context = ""
            try:
                # ValuePattern (Standard text boxes)
                value_pattern = element.GetPattern(auto.PatternId.ValuePattern)
                if value_pattern:
                    text_context = value_pattern.Value
                else:
                    # Fallback: Document/Text Pattern
                    # This can be slow, so we limit length
                    text_pattern = element.GetPattern(auto.PatternId.TextPattern)
                    if text_pattern:
                        # Get selection or visible range?
                        # Just getting document range is expensive.
                        # Optimization: Just assume empty context for non-standard apps for safety first
                        pass
                    else:
                        # Fallback: Name (often contains text for simple labels/elements)
                        text_context = element.Name
            except Exception as e:
                # print(f"Context fetch warning: {e}")
                pass

            return text_context, caret_x, caret_y, app_name

        except Exception as e:
            # print(f"Ctx Error: {e}") # Reduce spam
            return None, 0, 0, "Error"

if __name__ == "__main__":
    ctx = ContextProvider()
    time.sleep(2)
    print("Getting context...")
    print(ctx.get_focused_context())
