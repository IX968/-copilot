import uiautomation as auto
import time
import pyperclip

class ContextProvider:
    def __init__(self):
        pass

    def get_focused_context(self):
        """
        返回 (光标前文本，caret_x, caret_y, 应用名称)
        """
        try:
            element = auto.GetFocusedControl()
            if not element:
                print("No focused element")
                return None, 0, 0, "Unknown"

            # 1. 获取应用名称（修复 AttributeError）
            try:
                pid = element.ProcessId
                import psutil
                process = psutil.Process(pid)
                app_name = process.name()
            except ImportError:
                # 备用方案：如果 psutil 未安装（尽管 conda 上通常已安装）
                app_name = f"PID:{element.ProcessId}"
            except Exception:
                app_name = "UnknownApp"

            rect = element.BoundingRectangle
            
            # --- 回退到鼠标位置（稳定方案） ---
            # "幽灵文本"与"鼠标指针"的手动校准
            # DPI 缩放问题已在 UI Overlay 中修复
            # 我们相对于指针尖端保持轻微偏移
            OFFSET_X = 15  # 指针右侧
            OFFSET_Y = 15  # 指针尖端下方（标准行为）
            
            try:
                import win32api
                mx, my = win32api.GetCursorPos()
                caret_x = mx + OFFSET_X
                caret_y = my + OFFSET_Y
                app_name = f"{app_name} (Mouse)"
            except:
                caret_x, caret_y = 0, 0

            # 3. 获取上下文文本（Copilot 必备）
            # 基础实现：针对标准编辑控件
            text_context = ""
            try:
                # ValuePattern（标准文本框）
                value_pattern = element.GetPattern(auto.PatternId.ValuePattern)
                if value_pattern:
                    text_context = value_pattern.Value
                else:
                    # 备用方案：文档/文本模式
                    # 这可能很慢，所以我们限制长度
                    text_pattern = element.GetPattern(auto.PatternId.TextPattern)
                    if text_pattern:
                        # 获取选区或可见范围？
                        # 获取文档范围开销很大
                        # 优化：为了安全起见，对非标准应用暂时假设为空上下文
                        pass
                    else:
                        # 备用方案：Name 属性（简单标签/元素通常包含文本）
                        text_context = element.Name
            except Exception as e:
                # print(f"上下文获取警告：{e}")
                pass

            return text_context, caret_x, caret_y, app_name

        except Exception as e:
            # print(f"上下文错误：{e}") # 减少垃圾日志
            return None, 0, 0, "Error"

if __name__ == "__main__":
    ctx = ContextProvider()
    time.sleep(2)
    print("Getting context...")
    print(ctx.get_focused_context())
